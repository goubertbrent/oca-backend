from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

font = ImageFont.truetype('Courier New Bold.ttf', 50)
text_img = Image.new('RGBA', (2480,1176), (0,0,0,0))
draw = ImageDraw.Draw(text_img)
draw.text((1795, 290), '1 2 3 4 5 6 7 8   4 4', font=font, fill=(0,0,0,255))
draw.text((415, 1095), '+ + + 1 2 3 / 4 5 6 7 / 8 9 0 1 2 + + +', font=font, fill=(0,0,0,255))
background = Image.open("SEPA_NF.png")
background.paste(text_img, (0,0), text_img)
background.show()

