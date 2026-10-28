import { ArrowRight, ScanLine } from 'lucide-react';
import { BotanicalDecorations, HandArrow, Scribble } from '../App';
import PlantCarousel from '../components/PlantCarousel';
import DetectPage from './DetectPage';
export default function HomePage() {
 return <><div className="home-page page-enter"><BotanicalDecorations/><section className="home-hero"><div className="headline-wrap"><Scribble/><h1 tabIndex="-1"><span>Detect Plant Diseases</span><span>with a Single Leaf Photo</span></h1></div><p className="hero-description">Upload a leaf image to identify supported plant diseases,<br className="desktop-break"/> explore symptoms, and discover helpful plant-care guidance.</p><div className="handwritten scan-note">Scan<br/>a leaf<HandArrow/></div></section><PlantCarousel/><div className="home-action"><div className="handwritten free-note">Free to try<HandArrow className="arrow-free"/></div><div className="cta-ring"><a href="#detect" className="button button-primary main-cta"><ScanLine size={28}/>Detect a Leaf <ArrowRight size={22}/></a></div></div></div><section id="detect" className="reference-shell route-detect detection-section" aria-label="Detect a plant condition"><DetectPage/></section></>;
}

