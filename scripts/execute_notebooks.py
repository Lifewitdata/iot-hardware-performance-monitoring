"""Execute notebook Python cells locally without network sockets; capture actual rich outputs."""
from pathlib import Path
import contextlib,io,base64,os
import nbformat as n
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import IPython.display as ipd
P=Path(__file__).resolve().parents[1]
os.chdir(P)
for path in sorted((P/'notebooks').glob('*.ipynb')):
    print('Executing',path.name,flush=True)
    nb=n.read(path,as_version=4); namespace={'__name__':'__main__'}; count=0
    for cell in nb.cells:
        if cell.cell_type!='code': continue
        count+=1; outputs=[]
        def show(*args,**kwargs):
            for num in plt.get_fignums():
                fig=plt.figure(num); stream=io.BytesIO(); fig.savefig(stream,format='png',dpi=110,bbox_inches='tight')
                outputs.append(n.v4.new_output('display_data',data={'image/png':base64.b64encode(stream.getvalue()).decode(),'text/plain':'<matplotlib figure>'}))
                plt.close(fig)
        def display(*objects,**kwargs):
            for obj in objects:
                data={'text/plain':str(obj)}
                if hasattr(obj,'_repr_html_'):
                    html=obj._repr_html_()
                    if html is not None: data['text/html']=html
                if hasattr(obj,'_repr_markdown_'): data['text/markdown']=obj._repr_markdown_()
                outputs.append(n.v4.new_output('display_data',data=data))
        ipd.display=display; plt.show=show
        stream=io.StringIO()
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            exec(compile(cell.source,f'{path.name}:cell{count}','exec'),namespace)
        if stream.getvalue(): outputs.append(n.v4.new_output('stream',name='stdout',text=stream.getvalue()))
        cell.outputs=outputs; cell.execution_count=count
    nb.metadata['execution_method']='Python in-process execution with real stdout, DataFrame and matplotlib output capture; sockets unavailable in build environment.'
    n.write(nb,path)
    print('Completed',path.name,flush=True)
