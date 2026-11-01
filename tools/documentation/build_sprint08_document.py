"""Gera o PDF único das Sprints 01 a 08 com apresentação e capa atualizadas."""
import re
from html import escape
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'docs/sprint-08'
TMP = ROOT / 'tmp/sprint08/pdf'
TMP.mkdir(parents=True, exist_ok=True)
for name, file in [('Arial','arial.ttf'),('Arial-Bold','arialbd.ttf')]:
    pdfmetrics.registerFont(TTFont(name, 'C:/Windows/Fonts/' + file))
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Body8', fontName='Arial', fontSize=10, leading=14, spaceAfter=7))
styles.add(ParagraphStyle(name='Head8', fontName='Arial-Bold', fontSize=13, leading=17, spaceBefore=14, spaceAfter=8, keepWithNext=True))
styles.add(ParagraphStyle(name='Cell8', fontName='Arial', fontSize=8, leading=11))
styles.add(ParagraphStyle(name='Cover8', fontName='Arial-Bold', fontSize=25, leading=34, alignment=1, spaceAfter=15))
styles.add(ParagraphStyle(name='IntroTitle', fontName='Arial-Bold', fontSize=17, leading=21, spaceAfter=10))
styles.add(ParagraphStyle(name='IntroBody', fontName='Arial', fontSize=9.5, leading=13, spaceAfter=7))
styles.add(ParagraphStyle(name='IntroPart', fontName='Arial-Bold', fontSize=9.5, leading=12, spaceBefore=4, spaceAfter=2))
styles.add(ParagraphStyle(name='IntroItem', fontName='Arial', fontSize=9, leading=11.5, leftIndent=8, spaceAfter=1))


def para(text, style='Body8'):
    return Paragraph(escape(text.replace('`','')), styles[style])


def footer(canvas, doc):
    canvas.setFont('Arial', 8)
    canvas.drawCentredString(A4[0]/2, 26, f'RotaCerta | Grupo 04 | Sprints 01 a 08 | Página {100 + doc.page}')


def intro_footer(canvas, doc):
    canvas.setFont('Arial', 8)
    canvas.drawCentredString(A4[0]/2, 26, 'RotaCerta | Grupo 04 | Sprints 01 a 08 | Página 2')


def main():
    tests = (SOURCE/'evidencias/testes.txt').read_text(encoding='utf-8-sig')
    assert 'OK (skipped=1)' in tests and 'FAILED (' not in tests, 'Concluir testes antes do PDF.'
    count = int(re.search(r'Ran (\d+) tests', tests).group(1))
    front = (SOURCE/'evidencias/frontend.txt').read_text(encoding='utf-8-sig')
    assert '# fail 0' in front
    cover = [Spacer(1,50), para('UNINASSAU', 'Cover8'), para('Ciência da Computação | Turma 8NA | 2026.2'),
             Spacer(1,75), para('RotaCerta', 'Cover8'), para('Documento técnico cumulativo', 'Cover8'),
             para('Sprints 01 a 08 | Grupo 04', 'Cover8'), Spacer(1,35)]
    for name in ['Álvaro Jordão - 01748200','Arthur Sales - 01593811','Vinícius Trigueiro - 01794959','William Coelho de Morais - 01263977','Guilherme de Luna Barros - 01615925']:
        cover.append(para(name))
    SimpleDocTemplate(str(TMP/'cover.pdf'),pagesize=A4,rightMargin=48,leftMargin=48).build(cover)

    intro = [
        para('Apresentação', 'IntroTitle'),
        para('Este documento reúne as entregas das Sprints 01 a 08 do projeto RotaCerta. As sete primeiras partes registram o planejamento, a arquitetura, a estrutura funcional, os módulos de pedidos e entregas, a roteirização, o desempenho, o painel operacional, os relatórios e a rastreabilidade. A Parte VIII consolida as funcionalidades, as permissões, a usabilidade e as regras de negócio.', 'IntroBody'),
        para('As Partes I a VII mantêm o conteúdo entregue anteriormente. A Parte VIII demonstra a evolução prática da Sprint 08 com funcionalidades integradas, dados persistidos, evidências de execução e validações técnicas. Todas as telas e respostas mostradas nas Partes III a VIII foram capturadas do sistema em funcionamento.', 'IntroBody'),
        para('Sumário', 'IntroTitle'),
    ]
    toc = [
        ('Parte I  Sprint 01 Planejamento do projeto', [
            '1  Identificação da equipe',
            '2  Tema, problema, objetivos e público alvo',
            '3  Requisitos funcionais e não funcionais',
            '4  Casos de uso e Product Backlog',
            '5  Cronograma semanal revisado',
        ]),
        ('Parte II  Sprint 02 Arquitetura e modelagem', [
            '6  Arquitetura do sistema',
            '7  Diagrama de classes',
            '8  Modelo Entidade Relacionamento',
            '9  Modelo relacional',
            '10  Protótipos das telas',
            '11  Banco de dados e projeto no GitHub',
            '12  Avaliação sequencial e paralela',
            '13  Aderência às orientações da disciplina',
        ]),
        ('Parte III  Sprint 03 Estrutura inicial funcionando', [
            '14  Estrutura implementada',
            '15  Banco de dados conectado',
            '16  Login funcional',
            '17  Cadastro de usuários',
            '18  Controle de perfis',
            '19  CRUD principal: pedidos',
            '20  Execução local',
            '21  Testes automatizados',
            '22  Ajustes no planejamento e na modelagem',
            '23  Repositório GitHub',
            '24  Dificuldades encontradas e próximos passos',
        ]),
    ]
    for title, items in toc:
        intro.append(para(title, 'IntroPart'))
        intro.extend(para(item, 'IntroItem') for item in items)
    SimpleDocTemplate(str(TMP/'intro.pdf'), pagesize=A4, rightMargin=48, leftMargin=48, topMargin=40, bottomMargin=45).build(intro, onFirstPage=intro_footer)

    historical_footer = canvas.Canvas(str(TMP/'historical-footers.pdf'), pagesize=A4)
    for page_number in range(3, 101):
        historical_footer.setFillColor(colors.white)
        historical_footer.rect(0, 0, A4[0], 42, fill=1, stroke=0)
        historical_footer.setFillColor(colors.black)
        historical_footer.setFont('Arial', 8)
        historical_footer.drawCentredString(
            A4[0]/2, 26, f'RotaCerta | Grupo 04 | Sprints 01 a 08 | Página {page_number}'
        )
        historical_footer.showPage()
    historical_footer.save()
    story = [para('Parte VIII  Sprint 08 Consolidação funcional', 'Head8'),
             para(f'Validação final: {count - 1} testes de backend aprovados, um ignorado por ausência de GPU CUDA; 15 testes de frontend aprovados. Build de produção concluído e auditoria npm sem vulnerabilidades. As evidências usam uma base SQLite isolada e persistida, com a aplicação real em execução.'),
             para('Os registros anteriores documentam a evolução do projeto. As regras e decisões desta parte prevalecem onde houver alteração em relação às sprints anteriores.')]
    lines = (SOURCE/'README.md').read_text(encoding='utf-8').splitlines()
    i = 1
    code = False
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('```'):
            code = not code
            i += 1
            continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+', x) for x in cells):
                    rows.append([para(x,'Cell8') for x in cells])
                i += 1
            n = len(rows[0]); widths = [135,364] if n == 2 else [220] + [279/(n-1)]*(n-1)
            table = Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dce7f2')),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#d9d9d9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
            story += [table,Spacer(1,10)]
            continue
        if line.startswith('## '):
            story.append(para(line[3:],'Head8'))
        elif line:
            story.append(para(line))
        i += 1
    captions = [
        ('01_confirmacao.png','Confirmação da atribuição em lote','A interface informa o alcance da operação antes de atribuir os pedidos.'),
        ('02_atribuicao.png','Resultado da atribuição automática','Pedido elegível atribuído e pedido de 100 kg mantido pendente por falta de capacidade.'),
        ('03_rotas.png','Planejamento de rotas integrado','Rotas geradas a partir dos pedidos atribuídos e persistidas no banco.'),
        ('04_janelas.png','Janelas e previsões das entregas','As paradas mostram previsão de chegada, espera e atraso. As distâncias são geográficas.'),
        ('05_entregador.png','Entregador no celular','Rota iniciada com a conta do entregador. A confirmação de entrega foi verificada pela API.'),
        ('06_acesso_negado.png','Controle de permissões na interface','O entregador não acessa relatórios gerenciais. A API também bloqueia a consulta com HTTP 403.'),
        ('07_painel.png','Painel depois da execução','Indicadores consultados após atribuição, roteirização e confirmação de uma entrega.'),
        ('08_historico.png','Histórico da entrega','Consulta do pedido depois de confirmar a entrega. Eventos mantêm autor e horário.')]
    for file,title,caption in captions:
        story += [PageBreak(),para(title,'Head8'),para(caption)]
        im=Image(str(SOURCE/'assets'/file))
        scale=min(499/im.imageWidth,610/im.imageHeight)
        im.drawWidth=im.imageWidth*scale; im.drawHeight=im.imageHeight*scale
        story.append(im)
    SimpleDocTemplate(str(TMP/'sprint08.pdf'),pagesize=A4,leftMargin=48,rightMargin=48,topMargin=40,bottomMargin=65).build(story,onFirstPage=footer,onLaterPages=footer)
    previous=PdfReader(ROOT/'output/pdf/Grupo_04_RotaCerta_Sprints_01_a_07.pdf')
    historical_footers=PdfReader(TMP/'historical-footers.pdf')
    writer=PdfWriter()
    writer.append(str(TMP/'cover.pdf'))
    writer.append(str(TMP/'intro.pdf'))
    for page, overlay in zip(previous.pages[2:], historical_footers.pages):
        page.merge_page(overlay)
        writer.add_page(page)
    writer.append(str(TMP/'sprint08.pdf'))
    writer.add_metadata({'/Title':'Grupo 04 RotaCerta Sprints 01 a 08','/Author':'Equipe RotaCerta Grupo 04'})
    target=ROOT/'output/pdf/Grupo_04_RotaCerta_Sprints_01_a_08.pdf'
    writer.write(str(target))
    print(f'{target} | {len(writer.pages)} páginas')


if __name__ == '__main__':
    main()
