import json
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Image, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus import PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
import matplotlib.pyplot as plt
from tne.TNE import TNE

styles = getSampleStyleSheet()
spacer_blank = Spacer(1, 12)
spacer_enter = Spacer(1, 6)

#take in json file contents
#https://www.geeksforgeeks.org/json-load-in-python/
#https://docs.reportlab.com/reportlab/userguide/ch6_paragraphs/

# Initialize the TNE object
session = TNE(uid=UID, bucket_name=BUCKET, project=PROJECT, version=VERSION)

def pdf_maker(content, file_name):
    #create pdf object, set bounds
    pdf_buffer = BytesIO()

    #contains pdf_buffer or file_name
    pdf = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styleN = styles['Normal']

    #Create Cover Page
    styleT = ParagraphStyle(
        'Title',
        fontSize=24,
        fontName='Helvetica-Bold',
        alignment=1,
        spaceAfter=20,
        leading=28
    )
    story = []

    #TODO: delete when .model and .pdfformatter has been outfitted with optional cover page option
    story.append(Spacer(1, 100))
    story.append(Paragraph(file_name, styleT))
    story.append(Spacer(1, 100))
    story.append(PageBreak())

    #iterate through each section 
    for section in content["sections"]:
        content_type = section["type"]
        actual_content = section["content"]

        #TODO: Uncomment when .model and .pdfformatter has been outfitted with optional cover page option
        # if content_type == "cover page":
        #     story.append(Spacer(1, 100))
        #     story.append(Paragraph(document_name, styleT))
        #     story.append(Spacer(1, 100))
        #     story.append(PageBreak())
    
        if content_type == "raw text":
            #have text/paragraph added to pdf (story object)
            story.append(Paragraph(actual_content, styleN))
            story.append(spacer_blank)
            continue
        
        elif content_type == "table":
            #have table added into pdf
            lines = actual_content.strip().split("\n")
            headers = lines[0].split("|") # Extract headers
            rows = [line.split("|") for line in lines[1:]]  # Extract row
            
            table_content = [headers] + rows

            styleT = TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTNAME', (0, 1), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10)
            ])
            
            story.append(Table(table_content, style= styleT))
        
        elif content_type == "chart":
            #load in json formatted content into code
            chart_contents = json.loads(actual_content)

            #get the chart data
            chart_datasets = chart_contents['data']

            #get chart title
            chart_title_display = chart_contents['options']['title']['display']
            chart_title_text = chart_contents['options']['title']['text']

            if(chart_title_display):
                plt.title(chart_title_text)

            #depending on type of chart listed
            if(chart_contents['type'] == 'line'):
                print("LINE CHART")

                #get chart legend
                chart_legend = chart_contents['options']['legend']['display']

                #BUILD GRAPH HERE
                # get x lables
                x_axis = chart_datasets['labels']

                # get dataset label
                dataset_label = chart_datasets['datasets'][0]['label']

                #get dataset
                dataset = chart_datasets['datasets'][0]['data']

                #build the graph
                plt.plot(x_axis, dataset)
                plt.ylabel(dataset_label)

                if(chart_legend):
                    plt.legend()

                #plt.show()

                #Save chart to BytesIO buffer
                chart_stream = BytesIO()
                plt.savefig(chart_stream, format='png')
                plt.close()
                
                chart_stream.seek(0)

                img = Image(chart_stream, width = 400, height = 300)

                story.append(img)
            
            elif(chart_contents['type'] == 'bar'):
                #get x axis lables
                x_axis = chart_datasets['labels']

                #get dataset lables (y-axis)
                dataset_label = chart_datasets['datasets'][0]['label']

                #get the dataset
                dataset = chart_datasets['datasets'][0]['data']

                #build the bar chart
                plt.bar(x_axis, dataset)
                plt.xlabel('Years') #TODO: NEED TO FIX SO X-AXIS LABEL CAN BE SET
                plt.ylabel(dataset_label)

                #Save chart to BytesIO buffer
                chart_stream = BytesIO()
                plt.savefig(chart_stream, format='png')
                plt.close()
                                
                chart_stream.seek(0)
                img = Image(chart_stream, width = 400, height = 300)

                story.append(img)
        else:
            print("SOMETHING ELSE")
            continue
            
    pdf.build(story)
    #contains pdf_buffer or pdf
    session.upload_object(file_name, pdf_buffer)
    return file_name

#turn file into dictionary
json_contents = json.loads(PROCESS_INPUT)

file_name = json_contents["document_filename"]
content = json_contents

#call pdf_maker method
result = pdf_maker(content, file_name)
