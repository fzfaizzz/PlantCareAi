"""Regression cases for misleading scores and source confusion, not model accuracy."""
import io
from pathlib import Path
import sys

import numpy as np
from PIL import Image
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from plantcare_streamlit import analysis, ml_engine
from plantcare_streamlit.result import _report_html, result_copy, _care_groups
from plantcare_streamlit.services import AnalysisError, Settings


def picture():
    stream=io.BytesIO()
    Image.new('RGB',(100,100),(30,150,40)).save(stream,'JPEG')
    return stream.getvalue()


def old_guess(score=40.4):
    return {
        'status':'success','engine':'local_tensorflow','plant':'Potato','condition':'Late Blight',
        'confidence':score,'observations':['Catalog lesions were incorrectly called observed symptoms.'],
        'symptoms':['Water-soaked lesions'], 'care':['Remove infected leaves immediately.'],
        'prevention':['Apply a spray.'],'catalog':{'matched':True,'slug':'potato-late-blight'},
        'probabilities':{'Potato___Late_blight':score,'Potato___healthy':30.0,'Tomato___healthy':15.0},
    }


def test_404_percent_is_not_a_disease_diagnosis_or_a_symptom_observation():
    result=analysis.normalize_result(old_guess())
    assert result['status']=='uncertain'
    assert result['plant'] is None and result['condition'] is None
    assert result['confidence'] is None
    assert result['classifier']['candidate']['score']==40.4
    assert not result['observations'] and not result['symptoms']
    assert not result['care'] and not result['prevention']
    assert not result['catalog']['matched']
    assert result['top_predictions'][0]['class_id']=='Potato___Late_blight'


def test_high_softmax_alone_does_not_prove_a_known_species():
    result=analysis.normalize_result(old_guess(99.9))
    assert result['status']=='uncertain' and result['plant'] is None
    assert not result['classifier']['calibrated']
    assert analysis.normalize_result(result)==result


def test_old_browser_result_and_download_are_normalized_too():
    result,plant,condition,*_=result_copy(old_guess())
    assert plant=='Plant not confirmed' and condition=='Result inconclusive'
    groups=_care_groups(result)
    assert 'Catalog lesions' not in str(groups)
    report=_report_html(old_guess(),'data:image/jpeg;base64,test')
    assert 'Result inconclusive' in report
    assert 'Remove infected leaves immediately' not in report
    assert '40%' not in report


def test_configured_gemini_is_primary_without_invoking_local(monkeypatch):
    calls=[]
    monkeypatch.setattr(analysis,'analyze_image',lambda data,settings: calls.append(data) or {'status':'success','observations':['Visible green leaf']})
    monkeypatch.setattr(ml_engine,'predict_image',lambda *_:pytest.fail('Local classifier should not override Gemini'))
    result=analysis.analyze_leaf(picture(),Settings(api_key='PRIVATE-TEST',model='test'),engine='auto')
    assert result['engine']=='gemini_cloud' and len(calls)==1
    assert result['observations']==['Visible green leaf']


def test_cloud_failure_does_not_turn_a_local_guess_into_success(monkeypatch):
    def unavailable(*_):raise AnalysisError('gemini_rate_limited','The cloud quota is busy.',True)
    monkeypatch.setattr(analysis,'analyze_image',unavailable)
    monkeypatch.setattr(ml_engine,'predict_image',lambda *_:old_guess())
    result=analysis.analyze_leaf(picture(),Settings(api_key='PRIVATE-TEST',model='test'),engine='auto')
    assert result['status']=='uncertain' and not result['care']
    assert any('quota' in item for item in result['warnings'])
    assert 'PRIVATE-TEST' not in str(result)


def test_explicit_cloud_mode_keeps_error_and_missing_local_is_actionable(monkeypatch):
    def unavailable(*_):raise AnalysisError('gemini_authentication_error','Server credentials need attention.')
    monkeypatch.setattr(analysis,'analyze_image',unavailable)
    with pytest.raises(AnalysisError,match='Server credentials'):
        analysis.analyze_leaf(picture(),Settings(api_key='PRIVATE-TEST'),engine='gemini')
    def missing(*_):raise FileNotFoundError('private path')
    monkeypatch.setattr(ml_engine,'predict_image',missing)
    with pytest.raises(AnalysisError) as error:
        analysis.analyze_leaf(picture(),Settings(),engine='local')
    assert error.value.code=='model_unavailable' and 'private path' not in error.value.message


@pytest.mark.parametrize('predictions',[[[.4,.6]],[[float('nan'),.5]],[[1.2,-.2]],[[.2,.2]]])
def test_classifier_rejects_invalid_output_without_fabricating_labels(monkeypatch,predictions):
    labels={0:'Tomato___healthy',1:'Potato___healthy'}
    monkeypatch.setattr(ml_engine,'get_labels',lambda:labels)
    values=np.asarray(predictions)
    if predictions==[[.4,.6]]:
        monkeypatch.setattr(ml_engine,'get_labels',lambda:{0:'Tomato___healthy'})
    monkeypatch.setattr(ml_engine,'get_model',lambda:lambda batch,training=False:values)
    with pytest.raises(ValueError):ml_engine.predict_image(picture())
