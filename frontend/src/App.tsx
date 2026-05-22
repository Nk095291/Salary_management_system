import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <main className="app">
      <h1>React + Django</h1>
      <p>Frontend is running. Connect it to the Django API at <code>/api/</code>.</p>
      <button type="button" onClick={() => setCount((value) => value + 1)}>
        Count is {count}
      </button>
    </main>
  )
}

export default App
