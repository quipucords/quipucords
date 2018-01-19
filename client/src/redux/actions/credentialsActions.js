import { credentialsTypes as types } from '../constants';
import credentialsService from '../../services/credentialsService';

const getCredentialsError = (bool, message) => ({
  type: types.GET_CREDENTIALS_ERROR,
  error: bool,
  message: message
});

const getCredentialsLoading = bool => ({
  type: types.GET_CREDENTIALS_LOADING,
  loading: bool
});

const getCredentialsSuccess = data => ({
  type: types.GET_CREDENTIALS_SUCCESS,
  data
});

const getCredentials = () => {
  return function(dispatch) {
    dispatch(getCredentialsLoading(true));
    return credentialsService
      .getCredentials()
      .then(success => {
        dispatch(getCredentialsSuccess(success));
      })
      .catch(error => {
        dispatch(getCredentialsError(true, error.message));
      })
      .finally(() => dispatch(getCredentialsLoading(false)));
  };
};

export {
  getCredentialsError,
  getCredentialsLoading,
  getCredentialsSuccess,
  getCredentials
};
