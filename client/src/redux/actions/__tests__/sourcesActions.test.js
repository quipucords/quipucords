import { reducers } from '../../reducers';

describe('SourcesActions', () => {
  it('Get the initial state', () => {
    expect(reducers.sources.initialState).toBeDefined();
  });
});
