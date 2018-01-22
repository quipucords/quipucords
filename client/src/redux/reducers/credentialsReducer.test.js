import { credentialsTypes } from '../constants';
import credentialsReducer from './credentialsReducer';

describe('CredentialsReducer', function() {
  it('should return the initial state', () => {
    const initialState = {
      error: false,
      errorMessage: '',
      loading: true,
      data: []
    };

    expect(credentialsReducer(undefined, {})).toEqual(initialState);
  });

  it('should handle GET_CREDENTIALS_ERROR', () => {
    const dispatched = {
      type: credentialsTypes.GET_CREDENTIALS_ERROR,
      error: true,
      message: 'error message'
    };

    expect(credentialsReducer(undefined, dispatched).error).toEqual(
      dispatched.error
    );
    expect(credentialsReducer(undefined, dispatched).errorMessage).toEqual(
      dispatched.message
    );
  });

  it('should handle GET_CREDENTIALS_LOADING', () => {
    const dispatched = {
      type: credentialsTypes.GET_CREDENTIALS_LOADING,
      loading: false
    };

    expect(credentialsReducer(undefined, dispatched).loading).toEqual(
      dispatched.loading
    );
  });

  it('should handle GET_CREDENTIALS_SUCCESS', () => {
    const dispatched = {
      type: credentialsTypes.GET_CREDENTIALS_SUCCESS,
      data: ['test']
    };

    expect(credentialsReducer(undefined, dispatched).data).toEqual(
      dispatched.data
    );
  });
});
