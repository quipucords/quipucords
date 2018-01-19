import { sourcesTypes as types } from '../constants';
import sourcesService from '../../services/sourcesService';

const getSourcesError = (bool, message) => ({
  type: types.GET_SOURCES_ERROR,
  error: bool,
  message: message
});

const getSourcesLoading = bool => ({
  type: types.GET_SOURCES_LOADING,
  loading: bool
});

const getSourcesSuccess = data => ({
  type: types.GET_SOURCES_SUCCESS,
  data
});

const getSources = () => {
  return function(dispatch) {
    dispatch(getSourcesLoading(true));
    return sourcesService
      .getSources()
      .then(success => {
        dispatch(getSourcesSuccess(success));
      })
      .catch(error => {
        dispatch(getSourcesError(true, error.message));
      })
      .finally(() => dispatch(getSourcesLoading(false)));
  };
};

export { getSourcesError, getSourcesLoading, getSourcesSuccess, getSources };
