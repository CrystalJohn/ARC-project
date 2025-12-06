import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { HeroUIProvider } from '@heroui/react'
import './index.css'
import App from './App.jsx'
// import { Amplify } from 'aws-amplify';
// import config from './amplifyconfiguration.json';

// Amplify.configure(config);

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <HeroUIProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </HeroUIProvider>
  </StrictMode>,
)
