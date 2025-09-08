import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ApolloClient, InMemoryCache, ApolloProvider } from '@apollo/client'
import HomePage from './pages/HomePage'
const queryClient = new QueryClient()
const apolloClient = new ApolloClient({
uri: import.meta.env.VITE_GRAPHQL_URL || 'http://localhost:8000/graphql',
cache: new InMemoryCache(),
})
function App() {
return (
<ApolloProvider client={apolloClient}>
<QueryClientProvider client={queryClient}>
<BrowserRouter>
<Routes>
<Route path="/" element={<HomePage />} />
</Routes>
</BrowserRouter>
</QueryClientProvider>
</ApolloProvider>
)
}
export default App
