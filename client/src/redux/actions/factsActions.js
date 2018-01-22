import { factsTypes } from '../constants';
import reportsService from '../../services/factsService';

const addFactsError = (bool, message) => ({
  type: factsTypes.ADD_FACTS_ERROR,
  error: bool,
  message: message
});

const addFactsLoading = bool => ({
  type: factsTypes.ADD_FACTS_LOADING,
  loading: bool
});

const addFactsSuccess = data => ({
  type: factsTypes.ADD_FACTS_SUCCESS,
  data
});

const addFacts = () => {
  return function(dispatch) {
    dispatch(addFactsLoading(true));
    return reportsService
      .addFacts()
      .then(success => {
        dispatch(addFactsSuccess(success));
      })
      .catch(error => {
        dispatch(addFactsError(true, error.message));
      })
      .finally(() => dispatch(addFactsLoading(false)));
  };
};

export { addFactsError, addFactsLoading, addFactsSuccess, addFacts };
