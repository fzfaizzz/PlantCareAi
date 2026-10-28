from pathlib import Path
from PIL import Image
root=Path.cwd()
source=Path(r'C:\Users\akhta\Downloads')
output=root/'qa/reference-v2'
files={'home':'ChatGPT Image Oct 21, 2026, 06_51_58 PM.png','library':'ChatGPT Image Oct 21, 2026, 06_51_36 PM.png','detect':'ChatGPT Image Oct 21, 2026, 06_51_21 PM.png','about':'ChatGPT Image Oct 21, 2026, 06_51_05 PM.png'}
for name,filename in files.items():
 reference=Image.open(source/filename).convert('RGB')
 current=Image.open(output/(name+'.png')).convert('RGB')
 if reference.size!=current.size:
  reference=reference.resize(current.size,Image.Resampling.LANCZOS)
 Image.blend(reference,current,0.5).save(output/(name+'-overlay.png'))
print('Saved four 50% comparison overlays at qa/reference-v2/.')
