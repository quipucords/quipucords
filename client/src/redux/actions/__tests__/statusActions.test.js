import { reducers } from '../../reducers';

describe('StatusActions', () => {
  it('Get the initial state', () => {
    expect(reducers.status.initialState).toBeDefined();
  });
});
