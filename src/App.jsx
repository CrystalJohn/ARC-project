import { BrowserRouter, Routes, Route } from 'react-router-dom'

function Home() {
  return <div className="p-4">Home Page</div>
}

function About() {
  return <div className="p-4">About Page</div>
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App