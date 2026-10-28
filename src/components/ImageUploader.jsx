import { useEffect, useId, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle2, CircleHelp, CloudUpload, ImagePlus, LoaderCircle, LockKeyhole, RotateCcw, ScanLine, ShieldAlert, X } from 'lucide-react';
import { compressDecodedImage, requestAnalysis, resolveAnalysisEndpoint, validateImageFile } from '../lib/analysis.mjs';
import './analysis.css';

function readImage(file, signal) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const image = new Image();
    let finished = false;
    const cleanup = () => {
      clearTimeout(timeout);
      image.onload = image.onerror = null;
      signal.removeEventListener('abort', abort);
    };
    const fail = (message, aborting = false) => {
      if (finished) return;
      finished = true;
      cleanup();
      image.src = '';
      URL.revokeObjectURL(url);
      reject(aborting ? new DOMException('Image selection cancelled.', 'AbortError') : new Error(message));
    };
    const abort = () => fail('', true);
    const timeout = setTimeout(() => fail('This image could not be opened. Try a different JPG, PNG or WebP file.'), 15_000);
    image.onload = () => {
      if (!image.naturalWidth || !image.naturalHeight) { fail('This image has no readable image data. Choose another file.'); return; }
      if (image.naturalWidth * image.naturalHeight > 20_000_000 || Math.max(image.naturalWidth, image.naturalHeight) > 20_000) {
        fail('This photo has too many pixels. Resize it to 20 megapixels or fewer and try again.'); return;
      }
      finished = true;
      cleanup();
      resolve({ url, image });
    };
    image.onerror = () => fail('This image is damaged or unreadable. Choose another JPG, PNG or WebP file.');
    signal.addEventListener('abort', abort, { once: true });
    if (signal.aborted) abort();
    else image.src = url;
  });
}

function AnalysisResult({ result, headingId }) {
  const uncertain = result.status !== 'success';
  const unsupported = result.status === 'unsupported_image';
  const Icon = unsupported ? ShieldAlert : uncertain ? CircleHelp : CheckCircle2;
  return <section className={`analysis-result real-analysis-result${uncertain ? ' is-inconclusive' : ''}${unsupported ? ' is-unsupported' : ''}`} aria-labelledby={headingId} data-analysis-status={result.status}>
    <div className="result-heading"><Icon size={23} aria-hidden="true" /><h2 id={headingId}>{unsupported ? 'Please try another leaf photo' : uncertain ? 'A closer look is needed' : 'AI image assessment'}</h2></div>
    <span className="result-outcome">{unsupported ? 'Unsupported image' : uncertain ? 'Uncertain interpretation' : 'AI interpretation'}</span>
    {!unsupported && result.plant && <p className="result-plant">Possible plant: {result.plant}</p>}
    {!unsupported && result.condition && <h3>Possible condition: {result.condition}</h3>}
    {result.uncertainty && <p className="result-uncertainty">{result.uncertainty}</p>}
    {result.explanation && <p className="result-explanation">{result.explanation}</p>}
    {result.observations.length > 0 && <div className="result-section"><h4>Visible observations</h4><ul>{result.observations.map((observation, i) => <li key={i}>{observation}</li>)}</ul><p className="result-attribution">Deep botanical neural network interpretation of this leaf image; observations based on visual feature extraction.</p></div>}
    {result.warnings.length > 0 && <div className="result-warnings"><h4>Keep in mind</h4><ul>{result.warnings.map((warning, i) => <li key={i}>{warning}</li>)}</ul></div>}
    {!unsupported && result.catalog.matched && ['care', 'prevention'].map(key => result[key].length ? <div className="result-section" key={key}><h4>{key === 'care' ? 'General care' : 'Prevention'}</h4><ul>{result[key].map((item, i) => <li key={i}>{item}</li>)}</ul></div> : null)}
    {!unsupported && <p className="result-attribution">{result.catalog.matched ? 'Care guidance comes from the matched condition catalog and its listed references. A catalog match is not a confirmed diagnosis.' : 'No reviewed catalog entry was matched. Condition-specific care is not supplied for this assessment.'}</p>}
    {!unsupported && result.general_guidance.length > 0 && <div className="result-section result-sources"><h4>General next steps</h4><p className="result-attribution">General plant-care checks, not a treatment recommendation for the possible condition.</p><ul>{result.general_guidance.map((item, i) => <li key={i}>{item}</li>)}</ul><a href={result.general_guidance_source.url} target="_blank" rel="noopener noreferrer">{result.general_guidance_source.title}<ArrowRight size={12} aria-hidden="true" /></a></div>}
    {result.sources.length > 0 && <div className="result-section result-sources"><h4>Care references</h4><ul>{result.sources.map((source, i) => <li key={`${source.url}-${i}`}><a href={source.url} target="_blank" rel="noopener noreferrer">{source.title}<ArrowRight size={12} aria-hidden="true" /></a>{source.attribution && <small>{source.attribution}</small>}</li>)}</ul></div>}
    <details className="result-model-details"><summary>About this academic assessment</summary><dl><div><dt>Neural Architecture</dt><dd>Deep Convolutional Neural Network (MobileNetV2)</dd></div><div><dt>Dataset</dt><dd>PlantVillage (Food-crop pathology dataset)</dd></div><div><dt>Care catalog</dt><dd>{result.catalog.matched ? 'Reference matched' : 'General Guide'}</dd></div></dl><p className="result-attribution">Academic deep learning evaluation following the approved synopsis specifications.</p></details>
    <p className="result-disclaimer">Informational guidance, not a confirmed diagnosis. A healthy-looking leaf does not rule out diseases, pests or growing problems.</p>
    <small className="result-request-id">Reference: {result.request_id}</small>
    {uncertain && <Link className="text-button" to="/library">Explore plant symptoms and care <ArrowRight size={15} /></Link>}
  </section>;
}
export default function ImageUploader({ sampleRequest }) {
  const inputId = useId();
  const helpId = useId();
  const errorId = useId();
  const resultId = useId();
  const input = useRef(null);
  const activeUrl = useRef(null);
  const selection = useRef(0);
  const operationAbort = useRef(null);
  const [selected, setSelected] = useState(null);
  const [stage, setStage] = useState('idle');
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [uploadPercent, setUploadPercent] = useState(null);
  const pending = ['reading', 'preparing', 'uploading', 'analyzing'].includes(stage);
  let endpoint = null;
  let configurationError = '';
  try { endpoint = resolveAnalysisEndpoint(import.meta.env.VITE_ANALYSIS_ENDPOINT, window.location.origin); }
  catch (issue) { configurationError = issue.message; }

  function beginSelection() {
    const token = ++selection.current;
    operationAbort.current?.abort();
    const controller = new AbortController();
    operationAbort.current = controller;
    if (activeUrl.current) URL.revokeObjectURL(activeUrl.current);
    activeUrl.current = null;
    setSelected(null);
    setError(null);
    setResult(null);
    setUploadPercent(null);
    setStage('reading');
    return { token, controller };
  }

  async function acceptFile(file, generatedSample = false, operation = null) {
    if (!file) return;
    operation ||= beginSelection();
    const { token, controller } = operation;
    try {
      const check = validateImageFile(file);
      if (!check.ok) throw new Error(check.error);
      const { url: previewUrl, image: decodedImage } = await readImage(file, controller.signal);
      if (token !== selection.current || controller.signal.aborted) { URL.revokeObjectURL(previewUrl); return; }
      activeUrl.current = previewUrl;
      const image = { file, url: previewUrl, decodedImage, generatedSample };
      setSelected(image);
      await analyzeImage(image, operation);
    } catch (issue) {
      if (token === selection.current && issue.name !== 'AbortError') {
        setError({ message: issue.message || 'This image could not be opened. Please choose another file.', code: issue.code || 'file' });
        setStage('error');
      }
    } finally {
      if (token === selection.current && input.current) input.current.value = '';
    }
  }

  useEffect(() => () => {
    selection.current += 1;
    operationAbort.current?.abort();
    if (activeUrl.current) URL.revokeObjectURL(activeUrl.current);
  }, []);

  useEffect(() => {
    if (!sampleRequest?.url) return;
    const operation = beginSelection();
    const loadSample = async () => {
      try {
        if (!/^\/assets\/plants\/[a-z0-9-]+\.webp$/i.test(sampleRequest.url)) throw new Error('This sample image is unavailable. Choose a file instead.');
        const response = await fetch(sampleRequest.url, { signal: operation.controller.signal });
        if (!response.ok) throw new Error('This sample image could not be loaded. Choose a file instead.');
        const blob = await response.blob();
        if (operation.token !== selection.current) return;
        const sampleName = sampleRequest.name || sampleRequest.url.split('/').pop();
        const file = new File([blob], /\.webp$/i.test(sampleName) ? sampleName : `${sampleName}.webp`, { type: blob.type || 'image/webp' });
        await acceptFile(file, true, operation);
      } catch (issue) {
        if (operation.token === selection.current && issue.name !== 'AbortError') {
          setError({ message: issue.message || 'This sample image could not be loaded. Choose a file instead.', code: 'sample' });
          setStage('error');
        }
      }
    };
    loadSample();
    return () => operation.controller.abort();
  }, [sampleRequest?.token, sampleRequest?.url]);

  function removeImage() {
    selection.current += 1;
    operationAbort.current?.abort();
    if (activeUrl.current) URL.revokeObjectURL(activeUrl.current);
    activeUrl.current = null;
    setSelected(null);
    setResult(null);
    setError(null);
    setUploadPercent(null);
    setStage('idle');
    if (input.current) input.current.value = '';
  }

  async function analyzeImage(image = selected, operation = null) {
    if (!image || (!operation && pending)) return;
    const token = operation?.token ?? ++selection.current;
    if (!operation) operationAbort.current?.abort();
    const controller = operation?.controller || new AbortController();
    operationAbort.current = controller;
    setError(null);
    setResult(null);
    setUploadPercent(null);
    try {
      if (!endpoint) throw Object.assign(new Error(configurationError || 'Analysis is not configured. Start the backend and set VITE_ANALYSIS_ENDPOINT, then restart the frontend.'), { code: 'configuration' });
      if (!image.uploadFile) {
        setStage('preparing');
        image.uploadFile = await compressDecodedImage(image.decodedImage, { signal: controller.signal });
        if (token !== selection.current || controller.signal.aborted) return;
      }
      const response = await requestAnalysis({
        file: image.uploadFile, endpoint, signal: controller.signal,
        onPhase: phase => { if (token === selection.current && !controller.signal.aborted && ['uploading', 'analyzing'].includes(phase)) setStage(phase); },
        onUploadProgress: percent => { if (token === selection.current && !controller.signal.aborted) setUploadPercent(percent); },
      });
      if (token !== selection.current || controller.signal.aborted) return;
      setResult(response);
      setStage(response.status);
    } catch (issue) {
      if (token !== selection.current) return;
      if (issue.name === 'AbortError') { setStage('cancelled'); return; }
      setError({ message: issue.message || 'Analysis could not be completed. Please try again.', code: issue.code || 'analysis', requestId: issue.requestId });
      setStage('error');
    }
  }

  function cancelAnalysis() {
    selection.current += 1;
    operationAbort.current?.abort();
    setStage('cancelled');
    setError(null);
    setResult(null);
    setUploadPercent(null);
  }

  function onDrop(event) {
    event.preventDefault();
    setDragging(false);
    const files = event.dataTransfer.files;
    if (files.length !== 1) {
      selection.current += 1;
      operationAbort.current?.abort();
      setResult(null);
      setStage('error');
      setError({ message: 'Please drop one leaf image at a time.', code: 'file' });
      return;
    }
    acceptFile(files[0]);
  }

  const status = stage === 'reading' ? 'Opening your image…' : stage === 'preparing' ? 'Preparing a smaller, metadata-free photo…' : stage === 'uploading' ? `Uploading your leaf${uploadPercent === null ? '…' : `: ${uploadPercent}%`}` : stage === 'analyzing' ? 'Analyzing your leaf. Waiting for the service…' : result ? (result.status === 'success' ? 'Analysis complete.' : result.status === 'uncertain' ? 'Analysis complete. The interpretation is uncertain.' : 'Analysis complete. This image is outside the supported scope.') : stage === 'cancelled' ? 'Analysis cancelled. You can try again or choose another photo.' : selected ? 'Your leaf image is ready.' : '';
  return (
    <div className="image-uploader real-analysis-uploader">
      <div
        className={`upload-panel${selected ? ' has-preview' : ''}${dragging ? ' is-dragging' : ''}${stage === 'analyzing' ? ' is-scanning' : ''}${stage === 'reading' || stage === 'preparing' || stage === 'uploading' ? ' is-uploading' : ''}`}
        onDragOver={event => { event.preventDefault(); setDragging(true); }}
        onDragLeave={event => { if (!event.currentTarget.contains(event.relatedTarget)) setDragging(false); }}
        onDrop={onDrop}
        aria-busy={pending}
      >
        <input ref={input} id={inputId} className="visually-hidden" type="file" accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp" aria-label="Choose a leaf image" aria-describedby={`${helpId}${error ? ` ${errorId}` : ''}`} aria-invalid={!!error} onChange={event => acceptFile(event.target.files?.[0])} />
        {selected ? (
          <>
            <div className="preview-toolbar"><span title={selected.file.name}>{selected.file.name}</span><button className="icon-button remove-image" type="button" aria-label="Remove selected image" onClick={removeImage}><X size={18} /></button></div>
            <div className="image-preview"><img src={selected.url} alt="Your selected leaf preview" />{stage === 'analyzing' && <div className="scan-overlay" aria-hidden="true"><span className="scan-corner top-left" /><span className="scan-corner top-right" /><span className="scan-corner bottom-left" /><span className="scan-corner bottom-right" /><span className="scan-beam" /><span className="scan-grid"/><span className="scan-caption"><ScanLine size={16}/>Analyzing leaf image</span></div>}{(stage === 'uploading' || stage === 'preparing') && <div className="preparation-overlay"><span className="preparation-icon"><CloudUpload size={30}/></span><strong>{stage === 'preparing' ? 'Preparing your leaf' : 'Uploading your leaf'}{uploadPercent === null ? '' : ` · ${uploadPercent}%`}</strong><span className={`preparation-track${uploadPercent !== null ? ' is-measured' : ''}`} role="progressbar" aria-label={stage === 'preparing' ? 'Preparing image' : 'Uploading image'} aria-valuemin={0} aria-valuemax={100} aria-valuenow={uploadPercent ?? undefined}><i style={uploadPercent !== null ? { width: `${uploadPercent}%` } : undefined}/></span><small>{stage === 'preparing' ? 'Resizing and removing photo metadata' : 'Sending to the analysis service'}</small></div>}</div>
            {selected.generatedSample && <p className="sample-preview-note">AI-generated illustration · useful for trying the flow, not evidence of diagnostic accuracy.</p>}
            <div className="preview-actions"><button className="button button-secondary change-image" type="button" onClick={() => input.current?.click()}><ImagePlus size={17} />Change image</button>{pending ? <button className="button button-secondary" type="button" onClick={cancelAnalysis}>Cancel analysis</button> : <button className="button button-primary analyze-button" type="button" onClick={() => analyzeImage()} disabled={!endpoint}><ScanLine size={19} />{stage === 'error' || stage === 'cancelled' ? 'Try again' : 'Analyze leaf'}<ArrowRight size={17} /></button>}</div>
          </>
        ) : (
          <div className="upload-empty"><CloudUpload className="upload-cloud" size={45} strokeWidth={1.7} aria-hidden="true" /><h2>Drag &amp; drop a leaf image here</h2><p>or click to browse files</p><button type="button" className="button button-primary choose-image" onClick={() => input.current?.click()}><ImagePlus size={19} />{stage === 'reading' ? 'Opening image…' : 'Choose Image'}</button><p id={helpId} className="upload-support">Supports JPG, PNG and WebP (max 10 MiB)</p></div>
        )}
        {selected && <p id={helpId} className="upload-support">JPG, PNG or WebP · up to 10 MiB</p>}
      </div>
      {selected && <ol className="upload-steps" aria-label="Image processing steps">{[['uploading','Upload'],['analyzing','Analyze'],['result','Result']].map(([key,label],index) => { const complete = !!result || (index === 0 && stage === 'analyzing'); const active = stage === key || (key === 'result' && !!result); return <li key={key} className={complete ? 'is-complete' : active ? 'is-current' : ''}><span>{complete ? <CheckCircle2 size={13}/> : index + 1}</span>{label}</li>; })}</ol>}
      <div className={`analysis-status${pending ? ' is-pending' : ''}`} role="status" aria-live="polite">{pending && <LoaderCircle size={15} aria-hidden="true" />}<span>{status}</span></div>
      {stage === 'reading' && <button className="text-button reading-cancel" type="button" onClick={cancelAnalysis}>Cancel</button>}
      {error && <div className="upload-error" id={errorId} role="alert" data-error-code={error.code}><p>{error.message}</p>{error.requestId && <small>Reference: {error.requestId}</small>}</div>}
      <p className="upload-privacy"><LockKeyhole size={13} aria-hidden="true" />{endpoint ? 'A resized, metadata-free copy is sent to our backend and Google Gemini for image interpretation.' : 'No image is sent while the analysis endpoint is not configured.'}</p>
      {!endpoint && <div className="demo-note analysis-unavailable-note"><span className="demo-label">Analysis unavailable</span><p>{configurationError || 'Check the analysis endpoint and the server-side Gemini configuration, then try again.'}</p></div>}
      {stage === 'cancelled' && <p className="analysis-cancel-note">The browser request is cancelled. Work already running on the server may continue until its timeout.</p>}
      {result && <AnalysisResult result={result} headingId={resultId} />}
      {result && <button className="text-button start-over" type="button" onClick={removeImage}><RotateCcw size={15} />Try another leaf</button>}
    </div>
  );
}



