# AgentGuard Frontend

Next.js 14 frontend application for AgentGuard platform.

## Architecture

```
src/
├── api/              # API client and service layer
├── app/              # Next.js App Router pages
├── components/       # Shared UI components
├── core/            # Core utilities and configuration
├── hooks/           # Custom React hooks
├── lib/             # Third-party library configurations
├── modules/         # Feature modules
│   ├── agents/      # Agent Registry UI
│   ├── versions/    # Agent Versioning UI
│   └── tools/       # Tool Registry UI
├── styles/          # Global styles
└── types/           # TypeScript type definitions
```

## Modules

### Agent Registry Module
- `AgentList` - Browse and manage agents
- Filtering by status and execution mode
- Pagination support
- Create, update, and delete operations

### Agent Versioning Module
- `VersionList` - View agent version history
- Create immutable snapshots
- Expandable snapshot details
- Version timeline visualization

### Tool Registry Module
- `ToolList` - View registered tools
- Risk-level filtering
- JSON Schema viewer
- Safety indicators (destructive, reversible, requires confirmation)

## Getting Started

### Prerequisites
- Node.js 18+
- Backend API running on http://localhost:8000

### Installation

```bash
cd Frontend
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Build

```bash
npm run build
npm run start
```

## API Client

The frontend uses a centralized API client (`src/api/client.ts`) that:
- Handles authentication headers
- Normalizes error responses
- Provides type-safe endpoints
- Manages request/response transformations

### Usage Example

```typescript
import { agentsApi } from '@/api';

// List agents
const agents = await agentsApi.list({ status: 'active', page: 1 });

// Create agent
const newAgent = await agentsApi.create({
  name: 'My Agent',
  endpoint_url: 'https://example.com/agent',
  execution_mode: 'http',
});
```

## Type Safety

All API types are generated from backend Pydantic schemas and stored in `src/types/`:
- `agent.ts` - Agent Registry types
- `version.ts` - Agent Versioning types
- `tool.ts` - Tool Registry types

## Testing

```bash
# Unit tests
npm run test

# E2E tests
npm run test:e2e

# Type check
npm run type-check

# Lint
npm run lint
```

## Part 1 Status

✅ Type definitions complete
✅ API client implemented
✅ Agent List component functional
✅ Version List component functional
✅ Tool List component functional
✅ Home page with navigation
✅ Responsive design with Tailwind CSS

## Part 2 Preview

Part 2 will add:
- Agent Intelligence analysis UI
- Risk Profile visualization
- Scenario Generation interface
- Scenario Suite browser
- Coverage heatmaps
- Test Strategy configuration

## Technologies

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **React 18** - UI library
- **Fetch API** - HTTP client (built-in)

## Module Guidelines

Each feature module follows this structure:

```
modules/feature/
├── index.ts           # Public exports
├── FeatureList.tsx    # List/browse component
├── FeatureDetail.tsx  # Detail view
└── FeatureForm.tsx    # Create/edit form
```

## Contributing

1. Follow existing module structure
2. Use TypeScript strictly (no `any`)
3. Write tests for new components
4. Use Tailwind for styling (no custom CSS)
5. Follow Next.js 14 App Router conventions
6. Keep components focused and composable
