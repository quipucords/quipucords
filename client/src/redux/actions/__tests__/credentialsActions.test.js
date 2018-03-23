import expect from 'expect';
import { reducers } from '../../reducers';

describe('CredentialsActions', function() {
  it('Get the initial state', () => {
    expect(reducers.credentials.initialState).toBeDefined();
  });
});
