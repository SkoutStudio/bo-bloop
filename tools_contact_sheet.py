import sys, os
from PIL import Image
d=sys.argv[1]; out=sys.argv[2]
fs=sorted(f for f in os.listdir(d) if f.endswith('.png'))
cols=3; w,h=640,360
rows=(len(fs)+cols-1)//cols
W=Image.new('RGB',(cols*w,rows*h),'white')
for i,f in enumerate(fs): W.paste(Image.open(os.path.join(d,f)).resize((w,h)),((i%cols)*w,(i//cols)*h))
W.save(out)
