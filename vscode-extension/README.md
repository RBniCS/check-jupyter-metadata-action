```
npm install
npm run compile
node_modules/vsce/vsce package
code --install-extension notebook-close-runner-*.vsix
# search "Notebook close runner" in Settings CTRL + ,
# set the "Python script" path, typically $HOME/.jupyter/clean_notebook.py
```