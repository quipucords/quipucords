import { credentialsTypes } from '../constants';
import credentialsService from '../../services/credentialsService';

const getCredentialsError = (bool, message) => ({
  type: credentialsTypes.GET_CREDENTIALS_ERROR,
  error: bool,
  message: message
});

const getCredentialsLoading = bool => ({
  type: credentialsTypes.GET_CREDENTIALS_LOADING,
  loading: bool
});

const getCredentialsSuccess = data => ({
  type: credentialsTypes.GET_CREDENTIALS_SUCCESS,
  data
});

const getCredentials = () => {
  return function(dispatch) {
    dispatch(getCredentialsLoading(true));
    return credentialsService
      .getCredentials()
      .then(success => {
        dispatch(getCredentialsSuccess(success));
        dispatch(getCredentialsLoading(false));
      })
      .catch(error => {
        dispatch(getCredentialsError(true, error.message));
        dispatch(getCredentialsLoading(false));
      });
  };
};

export {
  getCredentialsError,
  getCredentialsLoading,
  getCredentialsSuccess,
  getCredentials
};
