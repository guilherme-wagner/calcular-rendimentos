from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle

from datetime import datetime

def gerar_pdf(df):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4
    )

    elementos = []

    estilos = getSampleStyleSheet()

    titulo_style = ParagraphStyle(
    "Titulo",
    parent=estilos["Title"],
    fontName="Helvetica-Bold",
    fontSize=20,
    leading=24,
    alignment=TA_LEFT,
    textColor=colors.HexColor("#1F2937"),
    spaceAfter=6
    )

    subtitulo_style = ParagraphStyle(
        "Subtitulo",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=12,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#6B7280"),
        spaceAfter=10
    )

    texto_style = ParagraphStyle(
        "Texto",
        parent=estilos["Normal"],
        fontSize=10,
        leading=18,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#374151")
    )

    secao_style = ParagraphStyle(
        "Secao",
        parent=estilos["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=colors.HexColor("#1F2937"),
        spaceBefore=10,
        spaceAfter=10
    )

    # Título
    elementos.append(
        Paragraph("Relatório de Rendimentos", titulo_style)
    )

    elementos.append(
        Paragraph(
            f"Gerado em {datetime.now():%d/%m/%Y %H:%M}",
            subtitulo_style
        )
    )

    elementos.append(Spacer(1, 18))

    # Cabeçalho da tabela
    dados = [[
        "Mês",
        "Ativo",
        "QTD",
        "Div/Cota",
        "Total",
        "DY (%)"
    ]]

    # Linhas
    for _, linha in df.iterrows():

        dados.append([
            linha["Mês"],
            linha["Ativo"],
            linha["QTD Cotas"],
            f"R$ {linha['Dividendo/Cota']:.2f}".replace(".", ","),
            f"R$ {linha['Total Recebido']:.2f}".replace(".", ","),
            f"{linha['DY (%)']:.2f}%".replace(".", ",")
        ])

    # Resumo
    total_recebido = df["Total Recebido"].sum()
    dy_medio = df["DY (%)"].mean()
    total_ativos = len(df)

    elementos.append(
        Paragraph("Resumo", secao_style)
    )

    elementos.append(
        Paragraph(
            f"Ativos Consultados: <b>{total_ativos}</b>",
            texto_style
        )
    )

    elementos.append(
        Paragraph(
            f"DY Médio: <b>{dy_medio:.2f}%</b>".replace(".", ","),
            texto_style
        )
    )

    elementos.append(
        Paragraph(
            f"Total Recebido: <b>R$ {total_recebido:.2f}</b>".replace(".", ","),
            texto_style
        )
    )

    elementos.append(Spacer(1, 15))

    # Tabela
    tabela = Table(
        dados,
        colWidths=[65, 110, 55, 80, 85, 55]
    )

    estilo = TableStyle([

        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Cabeçalho
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F46E5")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),

        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,0),10),

        ('BOTTOMPADDING',(0,0),(-1,0),10),
        ('TOPPADDING',(0,0),(-1,0),10),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),

        # Corpo
        ('FONTNAME',(0,1),(-1,-1),'Helvetica'),
        ('FONTSIZE',(0,1),(-1,-1),9),

        ('TEXTCOLOR',(0,1),(-1,-1),colors.HexColor("#374151")),

        # Apenas linhas horizontais
        ('LINEBELOW',(0,0),(-1,-1),0.3,colors.HexColor("#E5E7EB")),

        # Alinhamentos
        ('ALIGN', (0,0), (-1,0), 'CENTER'),   # Cabeçalho

        ('ALIGN', (0,1), (0,-1), 'CENTER'),   # Mês
        ('ALIGN', (1,1), (1,-1), 'CENTER'),     # Ativo
        ('ALIGN', (2,1), (2,-1), 'CENTER'),   # QTD
        ('ALIGN', (3,1), (5,-1), 'CENTER'),    # Valores

        ('BOTTOMPADDING',(0,1),(-1,-1),8),
        ('TOPPADDING',(0,1),(-1,-1),8),
    ])

    # Linhas alternadas
    for linha in range(1, len(dados)):

        cor = (
            colors.white
            if linha % 2
            else colors.HexColor("#F9FAFB")
        )

        estilo.add(
            'BACKGROUND',
            (0, linha),
            (-1, linha),
            cor
        )

    tabela.setStyle(estilo)

    elementos.append(tabela)

    doc.build(elementos)

    buffer.seek(0)

    return buffer