import { reducers } from '../../reducers';

describe('CredentialsActions', () => {
  it('Get the initial state', () => {
    expect(reducers.credentials.initialState).toBeDefined();
  });
});
