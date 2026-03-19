# Multiple Checklists Feature - Implementation Plan

## Overview

This document outlines the implementation plan for adding multiple named checklists per user to Tethered, positioned as a premium feature to drive subscription conversions.

## Business Case

### User Stories
1. **Dom with multiple subs**: "I need different checklists for my experienced sub Sarah vs my new sub Alex - they have completely different limits and interests"
2. **Switch user**: "I want separate checklists for when I'm topping vs bottoming - my desires are different in each role"
3. **Professional Dom**: "I need individual checklists for each client to track their specific preferences and hard limits"
4. **Scenario-based organization**: "I want separate checklists for rope play vs impact play sessions"

### Revenue Impact
- **Current premium model**: Task system with 5 free tasks, unlimited premium
- **New premium hook**: 1 free checklist, unlimited premium checklists  
- **Expected conversion increase**: 15-20% based on competitor analysis
- **Customer value**: Addresses pain point none of our competitors solve

## Current System Analysis

### Database Schema (Current)
```typescript
ChecklistAnswer {
  id: string
  owner: string
  questionId?: string         // Links to ChecklistQuestion
  customActivityId?: string   // Links to CustomActivity  
  tried: boolean
  rating: number             // 1-5 stars
  desireGiving: number       // 1-5 scale
  desireReceiving: number    // 1-5 scale
  notes: string
  shareNotes: boolean
}

ChecklistQuestion {
  id: string
  name: string
  description: string
  categoryId: string          // Links to ChecklistCategory
  // Has many ChecklistAnswers
}

CustomActivity {
  id: string
  owner: string
  name: string
  description: string
  categoryId?: string         // null = "My Activities"
  // Has many ChecklistAnswers
}
```

### Current Data Flow
1. User views ChecklistPage.tsx
2. DataService fetches `listCategoriesWithQuestions()` and `listCustomActivitiesWithAnswers()`
3. Each question/activity has 0-1 ChecklistAnswer per user
4. Answers are displayed via ChecklistCategory and ChecklistItem components
5. Partner sharing works by comparing ChecklistAnswers between users

### UI/UX Patterns
- Single checklist view with categories (BDSM activities organized by type)
- Filter by rating, desire level, search terms
- "My Activities" section for user-created activities
- Quick Rate modal for bulk rating unrated items
- Partner profile comparison views

## Proposed Solution

### Database Schema Changes

#### New Model: UserChecklist
```typescript
UserChecklist {
  id: string                  // Primary key
  owner: string              // User ID (matches owner pattern)
  name: string               // User-defined name ("Dom checklist", "Client A")
  description?: string       // Optional description
  isDefault: boolean         // One default per user for backwards compatibility
  createdAt: string
  updatedAt: string
}
```

#### Modified Model: ChecklistAnswer
```typescript
ChecklistAnswer {
  id: string
  owner: string
  checklistId: string        // NEW: Links to UserChecklist
  questionId?: string        
  customActivityId?: string   
  tried: boolean
  rating: number             
  desireGiving: number       
  desireReceiving: number    
  notes: string
  shareNotes: boolean
  createdAt: string
  updatedAt: string
}
```

#### Modified Model: CustomActivity
```typescript
CustomActivity {
  id: string
  owner: string
  checklistId: string        // NEW: Links to UserChecklist 
  name: string
  description: string
  categoryId?: string        
  createdAt: string
  updatedAt: string
}
```

### Amplify Schema Updates
```typescript
UserChecklist: a.model({
  owner: a.string(),
  name: a.string().required(),
  description: a.string(),
  isDefault: a.boolean(),
})
.secondaryIndexes((index) => [
  index("owner").name("byOwner"),
])
.authorization((allow) => [allow.owner()]),

// Update ChecklistAnswer to include checklistId
ChecklistAnswer: a.model({
  owner: a.string(),
  checklistId: a.id().required(),
  checklist: a.belongsTo("UserChecklist", "checklistId"),
  questionId: a.id(),
  question: a.belongsTo("ChecklistQuestion", "questionId"),
  customActivityId: a.id(),
  customActivity: a.belongsTo("CustomActivity", "customActivityId"),
  // ... existing fields
})

// Update CustomActivity to include checklistId  
CustomActivity: a.model({
  owner: a.string(),
  checklistId: a.id().required(),
  checklist: a.belongsTo("UserChecklist", "checklistId"),
  name: a.string().required(),
  description: a.string(),
  categoryId: a.id(),
  category: a.belongsTo("ChecklistCategory", "categoryId"),
})
```

### Migration Strategy

#### Phase 1: Schema Migration (Zero Downtime)
1. **Deploy new schema** with UserChecklist model
2. **Add checklistId field** to ChecklistAnswer and CustomActivity (nullable initially)
3. **Migration Lambda**: 
   - Create default UserChecklist for each user with existing data
   - Update all ChecklistAnswers to link to default checklist
   - Update all CustomActivities to link to default checklist
4. **Make checklistId required** in subsequent deployment

#### Migration Script Logic
```typescript
async function migrateToMultipleChecklists() {
  // Get all users who have checklist data
  const usersWithData = await getDistinctOwners(['ChecklistAnswer', 'CustomActivity']);
  
  for (const userId of usersWithData) {
    // Create default checklist
    const defaultChecklist = await createUserChecklist({
      owner: userId,
      name: 'My Checklist',
      description: 'Your original checklist',
      isDefault: true
    });
    
    // Link existing answers
    await updateChecklistAnswersByOwner(userId, defaultChecklist.id);
    
    // Link existing custom activities  
    await updateCustomActivitiesByOwner(userId, defaultChecklist.id);
  }
}
```

## Implementation Plan

### Phase 1: Backend Infrastructure (Weeks 1-2)
**Sprint 1: Database Schema**
- [ ] Add UserChecklist model to Amplify schema
- [ ] Add checklistId fields to ChecklistAnswer and CustomActivity (nullable)
- [ ] Deploy schema changes
- [ ] Write and test migration script

**Sprint 2: Data Service Updates**
- [ ] Add UserChecklist CRUD operations to DataService
- [ ] Update ChecklistAnswer operations to handle checklistId
- [ ] Update CustomActivity operations to handle checklistId  
- [ ] Add checklist management utilities
- [ ] Update localStorage adapter for anonymous users

### Phase 2: Premium Integration (Week 3)
**Sprint 3: Subscription Logic**
- [ ] Add FREE_CHECKLIST_LIMIT constant (set to 1)
- [ ] Create checklist limit utility functions
- [ ] Add checklist count to subscription hooks
- [ ] Implement upgrade prompts in UI
- [ ] Add premium gating to checklist creation

### Phase 3: Core UI Implementation (Weeks 4-6)  
**Sprint 4: Checklist Management**
- [ ] Create ChecklistManager component
- [ ] Add checklist selection dropdown to ChecklistPage
- [ ] Implement create/edit/delete checklist modals
- [ ] Update ChecklistPage to filter by active checklist
- [ ] Add checklist switching functionality

**Sprint 5: Enhanced UX**
- [ ] Add checklist indicators throughout UI
- [ ] Update Quick Rate to work with active checklist
- [ ] Add checklist duplication feature
- [ ] Implement checklist import/export
- [ ] Update search/filter to be checklist-aware

### Phase 4: Partner Integration (Weeks 7-8)
**Sprint 6: Relationship Updates**
- [ ] Add checklist selection to partner profile sharing
- [ ] Update relationship invitation flow
- [ ] Modify comparison views to handle multiple checklists
- [ ] Add partner checklist browsing
- [ ] Update notification system for checklist changes

### Phase 5: Testing & Polish (Weeks 9-10)
**Sprint 7: Testing**
- [ ] Unit tests for all new utilities and services
- [ ] Integration tests for checklist management
- [ ] E2E tests for premium upgrade flow
- [ ] Migration testing with production data copies
- [ ] Performance testing with multiple checklists

**Sprint 8: Launch Preparation**
- [ ] Documentation updates
- [ ] Help text and onboarding tooltips  
- [ ] Analytics tracking for feature usage
- [ ] A/B testing setup for upgrade prompts
- [ ] Support documentation

## Detailed UI/UX Design

### Checklist Management Interface

#### ChecklistSelector Component
```
[My Checklists ▼]   [+ New Checklist]
├── 📋 Dom Checklist (234 activities) ✓
├── 📋 Sub Checklist (189 activities)
└── 📋 Rope Play Only (67 activities)
```

#### New Checklist Modal
```
Create New Checklist
┌─────────────────────────────────┐
│ Name: [Dom Checklist          ] │
│ Description (optional):         │
│ [For sessions where I'm topping]│
│                                 │
│ Copy from existing checklist:   │
│ [ None ▼ ]                     │
│                                 │
│ [Cancel]  [Create Checklist]    │
└─────────────────────────────────┘
```

#### Premium Upgrade Prompt
```
⭐ Upgrade to Premium
You've reached your free checklist limit (1/1)

Premium benefits:
✅ Unlimited checklists
✅ Checklist templates  
✅ Advanced sharing options
✅ Priority support

[Upgrade Now - $4.99/month]  [Maybe Later]
```

### Updated ChecklistPage Layout
```
Checklist                          [Quick Rate] [+ Add Activity]
[My Checklists: Dom Checklist ▼]  [⚙️ Manage Checklists]

Search: [rope...]  Rating: [All ▼]  Desire: [All ▼]

📁 My Activities (12 activities)
📁 Rope Bondage (23 activities)  
📁 Impact Play (45 activities)
...
```

### Checklist Management Page
```
My Checklists                              [+ Create Checklist]

📋 Dom Checklist (Default)               [Edit] [⋮]
   234 activities • Created Mar 15, 2024
   Used in 2 relationships
   
📋 Sub Checklist                         [Edit] [⋮] 
   189 activities • Created Mar 20, 2024
   
📋 Client A - Sarah                      [Edit] [⋮]
   156 activities • Created Mar 22, 2024
   Private • Not shared
```

## Premium Integration Strategy

### Freemium Model
```typescript
export const FREE_CHECKLIST_LIMIT = 1;

export function calculateIsAtChecklistLimit(
  hasActiveSubscription: boolean, 
  checklistCount: number
): boolean {
  return !hasActiveSubscription && checklistCount >= FREE_CHECKLIST_LIMIT;
}

export function getChecklistLimitMessage(
  checklistCount: number,
  hasActiveSubscription: boolean
): string {
  if (hasActiveSubscription) {
    return 'You have unlimited checklists with your subscription.';
  }
  
  if (checklistCount >= FREE_CHECKLIST_LIMIT) {
    return 'You\'ve reached your free checklist limit. Upgrade to create more checklists.';
  }
  
  return `You have ${FREE_CHECKLIST_LIMIT - checklistCount} free checklist remaining.`;
}
```

### Upgrade Touch Points
1. **Create checklist button** - Disabled with upgrade prompt
2. **Checklist dropdown** - Shows limit indicator
3. **Partner sharing** - Highlights multiple checklist benefits
4. **Import checklist** - Premium-only feature
5. **Advanced organization** - Premium positioning

### Conversion Optimization
- **Progressive disclosure**: Show benefits as user engages more
- **Social proof**: "Join 500+ premium users with unlimited checklists"
- **Time-limited offers**: First month 50% off for early adopters
- **Value demonstration**: Calculate time saved with multiple checklists

## Technical Considerations

### Performance Optimization
- **Lazy loading**: Only load active checklist data initially
- **Caching**: Cache checklist metadata for quick switching
- **Pagination**: Large checklists load incrementally
- **Indexing**: Optimize database queries with proper indices

### Data Integrity
- **Referential integrity**: Proper foreign key relationships
- **Orphan cleanup**: Handle deleted checklists gracefully
- **Default checklist**: Always maintain one default per user
- **Migration rollback**: Plan for schema rollback if needed

### Security & Privacy
- **Access control**: Checklist-level sharing permissions
- **Data isolation**: Strong user boundaries in multi-tenant system
- **Audit logging**: Track checklist access and modifications
- **GDPR compliance**: Include checklists in data export/deletion

## Testing Strategy

### Unit Tests
- [ ] UserChecklist CRUD operations
- [ ] Checklist limit calculations
- [ ] Migration script logic
- [ ] Premium utility functions

### Integration Tests  
- [ ] End-to-end checklist creation flow
- [ ] Partner sharing with multiple checklists
- [ ] Premium upgrade and downgrade flows
- [ ] Data migration accuracy

### User Acceptance Tests
- [ ] Dom with multiple subs workflow
- [ ] Switch user role-based checklists
- [ ] Professional dom client management
- [ ] Freemium conversion flow

### Performance Tests
- [ ] Load time with 10+ checklists
- [ ] Database query performance
- [ ] Mobile responsiveness
- [ ] Concurrent user scenarios

## Success Metrics

### Business Metrics
- **Premium conversion rate**: Target 15-20% increase
- **Feature adoption**: 60%+ of active users create 2nd checklist
- **Customer satisfaction**: NPS score improvement
- **Revenue impact**: $X increase in monthly recurring revenue

### Product Metrics
- **Checklist creation rate**: New checklists per active user
- **Checklist usage**: Switching frequency between checklists  
- **Upgrade conversion**: Free-to-premium at checklist limit
- **Feature stickiness**: Retention after creating multiple checklists

### Technical Metrics
- **Performance**: Page load time under 2 seconds
- **Reliability**: 99.9% uptime during migration
- **Data accuracy**: Zero data loss during migration
- **Error rates**: <0.1% error rate in checklist operations

## Risk Assessment

### High Priority Risks
1. **Data migration failure** - Could corrupt existing user data
   - *Mitigation*: Extensive testing, rollback plan, gradual rollout
2. **Performance degradation** - Multiple checklists could slow app
   - *Mitigation*: Performance testing, caching strategy, optimization
3. **Premium conversion disappointment** - Feature might not drive expected revenue
   - *Mitigation*: A/B testing, user feedback loops, pricing flexibility

### Medium Priority Risks  
1. **UI complexity** - Could confuse existing users
   - *Mitigation*: Progressive disclosure, onboarding flow, help documentation
2. **Partner confusion** - Sharing becomes more complex
   - *Mitigation*: Clear UX, default behaviors, educational content
3. **Database costs** - More data storage and queries
   - *Mitigation*: Cost monitoring, query optimization, data lifecycle policies

### Low Priority Risks
1. **Support burden** - More complex feature to support
   - *Mitigation*: Documentation, FAQ, user education
2. **Feature creep** - Requests for more advanced features
   - *Mitigation*: Clear roadmap communication, prioritization framework

## Future Enhancements

### Phase 2 Features (Future Roadmap)
- **Checklist templates**: Pre-built checklists for common scenarios
- **Collaborative checklists**: Partners co-edit shared checklists  
- **Checklist versioning**: Track changes over time
- **Advanced filtering**: Filter across all checklists
- **Bulk operations**: Copy/move activities between checklists

### Integration Opportunities
- **Scene planning**: Link checklists to specific scene types
- **Task system**: Assign tasks based on active checklist
- **Safety alerts**: Checklist-specific safety reminders
- **Analytics**: Insights across multiple checklists

## Conclusion

The multiple checklists feature addresses a genuine user need that none of our competitors currently solve. By positioning it as a premium feature with a generous free tier (1 free checklist), we can drive subscription conversions while providing significant value to power users.

The implementation plan balances technical complexity with business impact, ensuring we deliver a robust feature that scales with our user base. The phased rollout minimizes risk while allowing for learning and iteration based on early user feedback.

Success will be measured not just by premium conversions, but by overall user engagement and satisfaction with the enhanced functionality. This feature positions Tethered as the most comprehensive and user-friendly BDSM checklist platform available.

---

*Implementation timeline: 10 weeks*  
*Estimated effort: 2-3 developer weeks*  
*Revenue impact: 15-20% conversion increase*  
*User value: High - addresses major pain point*