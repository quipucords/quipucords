import { reducers } from '../../reducers';

describe('ReportsActions', () => {
  it('Get the initial state', () => {
    expect(reducers.reports.initialState).toBeDefined();
  });
});
