import helpers from '../../common/helpers';
import { sourcesTypes } from '../constants';

const initialState = {
  persist: {
    selectedSources: []
  },

  view: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    sources: []
  }
};

const sourcesReducer = function(state = initialState, action) {
  switch (action.type) {
    // Persist
    case sourcesTypes.SOURCES_SELECTED:
      return helpers.setStateProp(
        'persist',
        {
          selectedSources: action.selectedSources
        },
        {
          state,
          reset: false
        }
      );

    // Error/Rejected
    case sourcesTypes.GET_SOURCES_REJECTED:
      return helpers.setStateProp(
        'view',
        {
          error: action.payload.error,
          errorMessage: action.payload.message
        },
        {
          state,
          initialState
        }
      );

    // Loading/Pending
    case sourcesTypes.GET_SOURCES_PENDING:
      return helpers.setStateProp(
        'view',
        {
          pending: true
        },
        {
          state,
          initialState
        }
      );

    // Success/Fulfilled
    case sourcesTypes.GET_SOURCES_FULFILLED:
      return helpers.setStateProp(
        'view',
        {
          sources: action.payload.results,
          fulfilled: true
        },
        {
          state,
          initialState
        }
      );

    default:
      return state;
  }
};

export { initialState, sourcesReducer };

export default sourcesReducer;
