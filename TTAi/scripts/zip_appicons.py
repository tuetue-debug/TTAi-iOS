import os, zipfile
root = r"C:\Users\vannt-pc\.openclaw\workspace\TTAi\Resources"
appicon = os.path.join(root, 'AppIcon.appiconset')
zip_path = os.path.join(root, 'TTAi_AppIcon_Placeholder.zip')
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for folder, _, files in os.walk(appicon):
        for file in files:
            full_path = os.path.join(folder, file)
            rel_path = os.path.relpath(full_path, root)
            zf.write(full_path, rel_path)
print('Zipped to', zip_path)
