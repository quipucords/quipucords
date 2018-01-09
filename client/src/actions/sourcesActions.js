
import * as types from '../constants/sourcesConstants';
import sourcesApi from '../services/sourcesApi';

const loadSourcesSuccess = data => ({
  type: types.LOAD_SOURCES_SUCCESS,
  data
});

const getSources = () => {
  return function(dispatch) {
    return sourcesApi.getSources().then(success => {
      dispatch(loadSourcesSuccess(success));
    }).catch(error => {
      throw(error);
    });
  };
};

export {
  loadSourcesSuccess,
  getSources
};
