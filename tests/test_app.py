from streamlit.testing.v1 import AppTest
from src.config import ROOT

def test_dashboard_loads_and_filters():
    app=AppTest.from_file(str(ROOT/'app/streamlit_app.py'),default_timeout=40).run()
    assert not app.exception
    assert len(app.tabs)==4
    assert len(app.metric)==4
    app.sidebar.selectbox[0].set_value('mahalanobis').run()
    app.sidebar.selectbox[1].set_value('Oil_temperature').run()
    assert not app.exception
