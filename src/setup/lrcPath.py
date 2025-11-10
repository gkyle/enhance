import os

current_directory = os.getcwd()
dotPath = os.path.join(current_directory, 'enhanceAI.lrdevplugin/PluginPath.txt')
# Determine if OS in Windows
if os.name == 'nt':
    lrcPath = os.path.join(current_directory, "run.bat")
else:
    lrcPath = os.path.join(current_directory, "run.sh")

with open(dotPath, 'w') as file:
    file.write(lrcPath)
    file.close()