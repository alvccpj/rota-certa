"""Janela de atendimento, persistência e evolução incremental do esquema."""
from datetime import datetime, timedelta, timezone
from unittest import TestCase
from unittest.mock import patch

from sqlalchemy import create_engine, text, inspect

from api_base import ApiTestCase
from app import database, planning
from app.models import Order, Route, RouteStop
from app.optimizer.routing import Stop


class SchedulingTestCase(TestCase):
    def test_wait_propagates_and_lateness_is_reported(self):
        start = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
        first = Order(id=101, latitude=0, longitude=0, desired_start=start + timedelta(minutes=30),
                      desired_end=start + timedelta(minutes=40))
        second = Order(id=102, latitude=0, longitude=0, desired_end=start + timedelta(minutes=32))
        route = Route(stops=[RouteStop(order=first), RouteStop(order=second)])
        planning.schedule(route, Stop('depot', 0, 0), start)
        self.assertEqual(route.stops[0].waiting_minutes, 30)
        self.assertEqual(route.stops[0].estimated_arrival, first.desired_start)
        self.assertEqual(planning.timing_info(route.stops[0])['timing_status'], 'ON_TIME')
        self.assertEqual(planning.timing_info(route.stops[1])['delay_minutes'], 3)
        self.assertEqual(route.estimated_duration_min, 40)

    def test_naive_database_dates_and_no_window(self):
        start = datetime(2026, 11, 1, 12)
        order = Order(id=1, latitude=0, longitude=0)
        route = Route(stops=[RouteStop(order=order)])
        planning.schedule(route, Stop('depot', 0, 0), start)
        self.assertEqual(planning.timing_info(route.stops[0])['timing_status'], 'NO_WINDOW')
        self.assertEqual(route.stops[0].waiting_minutes, 0)
        self.assertEqual(route.estimated_duration_min, 5)

    def test_upgrade_preserves_old_rows_and_can_be_repeated(self):
        engine = create_engine('sqlite://')
        with engine.begin() as connection:
            connection.execute(text('CREATE TABLE route_stops (id INTEGER PRIMARY KEY)'))
            connection.execute(text('INSERT INTO route_stops (id) VALUES (7)'))
        with patch.object(database, 'engine', engine):
            database.upgrade_schema()
            database.upgrade_schema()
        self.assertIn('waiting_minutes', [x['name'] for x in inspect(engine).get_columns('route_stops')])
        with engine.connect() as connection:
            self.assertEqual(tuple(connection.execute(text('SELECT id, waiting_minutes FROM route_stops')).one()), (7, 0))
        engine.dispose()


class SchedulingApiTestCase(ApiTestCase):
    def test_generated_wait_survives_a_new_database_session(self):
        future = datetime.now(timezone.utc) + timedelta(hours=3)
        created = self.client.post('/orders', headers=self.admin, json=self.order_payload(
            assigned_courier_id=self.courier_id(), desired_start=future.isoformat(),
            desired_end=(future + timedelta(hours=1)).isoformat()))
        self.assertEqual(created.status_code, 201, created.text)
        response = self.client.post('/routes/generate', headers=self.admin, json={'mode': 'SEQUENTIAL'})
        self.assertEqual(response.status_code, 200, response.text)
        routes = self.client.get('/routes', headers=self.admin).json()['routes']
        stop = next(s for r in routes for s in r['stops'] if s['order_id'] == created.json()['id'])
        self.assertGreater(stop['waiting_minutes'], 0)
        self.assertEqual(stop['timing_status'], 'ON_TIME')
        self.assertEqual(datetime.fromisoformat(stop['estimated_arrival']), future)
