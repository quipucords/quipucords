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

const addCredentialLoading = bool => ({
  type: credentialsTypes.ADD_CREDENTIAL_LOADING,
  loading: bool
});

const addCredentialSuccess = data => ({
  type: credentialsTypes.ADD_CREDENTIAL_SUCCESS,
  data
});

const addCredentialError = (bool, message) => ({
  type: credentialsTypes.ADD_CREDENTIAL_ERROR,
  error: bool,
  message: message
});

const addCredential = (data, addCallback) => {
  return function(dispatch) {
    dispatch(addCredentialLoading(true));
    return credentialsService
      .addCredential(data)
      .then(success => {
        dispatch(addCredentialSuccess(success));
        dispatch(addCredentialLoading(false));
        if (addCallback) {
          addCallback(false, success);
        }
      })
      .catch(error => {
        dispatch(addCredentialError(true, error.message));
        dispatch(addCredentialLoading(false));
        if (addCallback) {
          addCallback(true, error.message);
        }
      });
  };
};

const updateCredentialLoading = bool => ({
  type: credentialsTypes.UPDATE_CREDENTIAL_LOADING,
  loading: bool
});

const updateCredentialSuccess = data => ({
  type: credentialsTypes.UPDATE_CREDENTIAL_SUCCESS,
  data
});

const updateCredentialError = (bool, message) => ({
  type: credentialsTypes.UPDATE_CREDENTIAL_ERROR,
  error: bool,
  message: message
});

const updateCredential = (data, addCallback) => {
  return function(dispatch) {
    dispatch(updateCredentialLoading(true));
    return credentialsService
      .updateCredential(data)
      .then(success => {
        dispatch(updateCredentialSuccess(success));
        dispatch(updateCredentialLoading(false));
        if (addCallback) {
          addCallback(false, success);
        }
      })
      .catch(error => {
        dispatch(updateCredentialError(true, error.message));
        dispatch(updateCredentialLoading(false));
        if (addCallback) {
          addCallback(true, error.message);
        }
      });
  };
};

export {
  getCredentialsError,
  getCredentialsLoading,
  getCredentialsSuccess,
  getCredentials,
  addCredentialError,
  addCredentialLoading,
  addCredentialSuccess,
  addCredential,
  updateCredentialError,
  updateCredentialLoading,
  updateCredentialSuccess,
  updateCredential
};
