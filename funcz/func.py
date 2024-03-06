from PIL import Image, ImageDraw, ImageFont
import io
from io import BytesIO
import requests
import random
def generate_health_bar(health_percentage):
    health_bar_image = Image.open("image.png")
    resized_health_bar = health_bar_image.resize((400, 15))
    bar_length = int(resized_health_bar.width * health_percentage / 100)
    cropped_health_bar = resized_health_bar.crop((0, 0, bar_length, resized_health_bar.height))

    return cropped_health_bar

def genbimg(name1,name2,hp1,hp2,psh1,psh2,n1,n2,sp1,sp2,opp,):
    print("here 15")

    health_bar1 = generate_health_bar(int(hp1))
    health_bar2 = generate_health_bar(int(hp2))
    combined_image = Image.open("arena.jpg")

    if int(psh1)==1:
      p1=f"https://raw.githubusercontent.com/poketwo/data/master/sprites/back-shiny/{sp1}.png"
    else:
      p1=f"https://raw.githubusercontent.com/poketwo/data/master/sprites/back/{sp1}.png"
    if int(psh2)==1:
      p2=f"https://raw.githubusercontent.com/poketwo/data/master/sprites/front-shiny/{sp2}.png"
    else:
      p2=f"https://raw.githubusercontent.com/poketwo/data/master/sprites/front/{sp2}.png"
    res1=requests.get(p1)
    res2=requests.get(p2)
    pk1=Image.open(BytesIO(res1.content))
    pk2=Image.open(BytesIO(res2.content)).convert("RGBA")
    w,h=pk2.size 
    pk1=pk1.resize((560,560)).convert("RGBA")
    pk2=pk2.resize((380,380))
    combined_image.paste(pk1,(50,230),pk1)
    combined_image.paste(pk2,(710,240),pk2)
    ball = Image.open("ball.png").convert("RGBA")

    combined_image.paste(health_bar2, (100,180))

    combined_image.paste(health_bar1, (740, 640))

    for i in range(n2):
      combined_image.paste(ball,(100+i*50,200),ball)
    for i in range(n1):
      combined_image.paste(ball,(740+i*50,660),ball)
    draw = ImageDraw.Draw(combined_image)
    font = ImageFont.truetype("Emizen.ttf", 50)
    font2 = ImageFont.truetype("Emizen.ttf", 40)
    font3 = ImageFont.truetype("Emizen.ttf", 30)
    draw.text((100,110), name2, fill="white", font=font)
    draw.text((740, 570), name1, fill="white", font=font)
    draw.text((1080, 230), opp, fill="white", font=font3)
    draw.text((520, 160), f"{hp2}%", fill="white", font=font2)
    draw.text((1150, 610), f"{hp1}%", fill="white", font=font2)

    # Save the cropped image
    n=random.randint(1,1000)
    combined_image.save(f"gen.png")
    return f"gen.png"



