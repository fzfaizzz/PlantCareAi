from PIL import Image
from pathlib import Path
import shutil, json
root=Path.cwd()
source=Path(r'C:\Users\akhta\.codex\generated_images\01a162ba-1f4c-7be3-8a96-829d9633618c')
files={
 'tomato-healthy':'exec-e18e9898-77f0-412b-84ff-4c2458a90cb3.png',
 'tomato-early-blight':'exec-a18029fc-2bdc-483a-9388-d620f618fad8.png',
 'potato-late-blight':'exec-0fbbd882-8bfc-4b2e-ab7b-8b584a90b7ae.png',
 'apple-scab':'exec-48cdcb5c-9076-4f89-b055-6fbf113b2a2c.png',
 'corn-common-rust':'exec-ea6cd55d-209a-4cd0-8335-495907bfe770.png',
 'grape-powdery-mildew':'exec-a8daf307-36f4-4339-ba79-e060718d4d8c.png',
 'healthy-dew-leaf':'exec-acabc5ed-941f-4bcb-b318-cdbab328e3a6.png'
}
subjects={
 'tomato-healthy':'Healthy serrated tomato leaf, green veins, tiny dew drops, blurred red tomato garden background.',
 'tomato-early-blight':'Tomato leaf, yellowing green surface with irregular brown blight-like patches and concentric rings, red tomatoes behind.',
 'potato-late-blight':'Broad oval potato leaf with irregular dark brown edge lesions, yellowing around patches, garden bokeh.',
 'apple-scab':'Oval serrated apple leaf with olive-green and brown scab-like spots, red apples behind.',
 'corn-common-rust':'Long corn blade diagonally across frame, parallel veins and small orange-brown elongated rust pustules, corn field bokeh.',
 'grape-powdery-mildew':'Five-lobed grape leaf with irregular white powdery coating, purple grapes behind.',
 'healthy-dew-leaf':'Extreme macro healthy dark green ovate leaf, luminous veins, clear dew drops, rich green background.'
}
records=[]
for name,filename in files.items():
 original=root/'asset-originals'/(name+'.png')
 original.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(source/filename,original)
 output=root/'public/assets/plants'/(name+'.webp')
 output.parent.mkdir(parents=True,exist_ok=True)
 with Image.open(original) as im:
  im.thumbnail((720,1080),Image.Resampling.LANCZOS)
  im.save(output,'WEBP',quality=86,method=6)
 records.append({'name':name,'file':str(output.relative_to(root)).replace('\\','/'),'original':str(original.relative_to(root)).replace('\\','/'),'generator':'built-in image_gen','prompt':'Use case: photorealistic-natural. ONE standalone 2:3 portrait premium botanical macro photograph. '+subjects[name]+' Natural morning light, realistic anatomy, fresh sage and forest greens. No text, watermark, UI, frame, collage, or panels.','illustrative':True,'visuallyInspected':True})
(root/'assets-home-generation.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print('Saved and optimized',len(records),'individually generated carousel assets.')
