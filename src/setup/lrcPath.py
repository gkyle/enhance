import os

current_directory = os.getcwd()
dotPath = os.path.join(current_directory, 'enhanceAI.lrdevplugin/PluginPath.txt')
lrcPath = os.path.join(current_directory, "run.bat")

with open(dotPath, 'w') as file:
    file.write(lrcPath)
    file.close()