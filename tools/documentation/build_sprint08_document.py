"""Gera o PDF único 01 a 08 preservando integralmente as entregas anteriores."""
import re
from html import escape
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
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


def para(text, style='Body8'):
    return Paragraph(escape(text.replace('`','')), styles[style])


def footer(canvas, doc):
    canvas.setFont('Arial', 8)
    canvas.drawCentredString(A4[0]/2, 26, f'RotaCerta | Grupo 04 | Sprint 08 | Página {100 + doc.page}')


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
    cover += [Spacer(1,25), para('Consolidação em 01/11/2026. As Sprints 01 a 07 são preservadas nas páginas 2 a 100, com seus registros históricos. A Sprint 08 inicia na página 101 e registra o escopo vigente e suas evidências.'),
              para('Envio no Teams pelo Scrum Master após revisão da equipe.')]
    SimpleDocTemplate(str(TMP/'cover.pdf'),pagesize=A4,rightMargin=48,leftMargin=48).build(cover)
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
    writer=PdfWriter()
    writer.append(str(TMP/'cover.pdf'))
    writer.append(previous,pages=(1,len(previous.pages)))
    writer.append(str(TMP/'sprint08.pdf'))
    writer.add_metadata({'/Title':'Grupo 04 RotaCerta Sprints 01 a 08','/Author':'Equipe RotaCerta Grupo 04'})
    target=ROOT/'output/pdf/Grupo_04_RotaCerta_Sprints_01_a_08.pdf'
    writer.write(str(target))
    print(f'{target} | {len(writer.pages)} páginas')


if __name__ == '__main__':
    main()
