import { credentialsTypes as types } from '../constants';
import * as actions from './credentialsActions';

describe('CredentialsActions', function() {
  it('should create a GET error action', () => {
    const error = true;
    const expectedAction = {
      type: types.GET_CREDENTIALS_ERROR,
      error,
      message: undefined
    };

    expect(actions.getCredentialsError(error)).toEqual(expectedAction);
  });

  it('should create a GET loading action', () => {
    const loading = true;
    const expectedAction = {
      type: types.GET_CREDENTIALS_LOADING,
      loading
    };

    expect(actions.getCredentialsLoading(loading)).toEqual(expectedAction);
  });

  it('should create a GET success action', () => {
    const data = {};
    const expectedAction = {
      type: types.GET_CREDENTIALS_SUCCESS,
      data
    };

    expect(actions.getCredentialsSuccess(data)).toEqual(expectedAction);
  });
});
