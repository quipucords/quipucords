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
  },

  update: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    source: null,
    sourceType: '',
    show: false,
    add: false,
    edit: false,
    delete: false
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

    // Show/Hide
    case sourcesTypes.CREATE_SOURCE_SHOW:
      return helpers.setStateProp(
        'update',
        {
          show: true,
          add: true
        },
        {
          state,
          initialState
        }
      );

    case sourcesTypes.EDIT_SOURCE_SHOW:
      return helpers.setStateProp(
        'update',
        {
          show: true,
          edit: true,
          source: action.source
        },
        {
          state,
          initialState
        }
      );

    case sourcesTypes.UPDATE_SOURCE_HIDE:
      return helpers.setStateProp(
        'update',
        {
          show: false
        },
        {
          state,
          initialState
        }
      );

    // Error/Rejected
    case sourcesTypes.ADD_SOURCE_REJECTED:
      return helpers.setStateProp(
        'update',
        {
          error: action.error,
          errorMessage: action.payload.message,
          add: true
        },
        {
          state,
          initialState
        }
      );

    case sourcesTypes.DELETE_SOURCE_REJECTED:
    case sourcesTypes.DELETE_SOURCES_REJECTED:
      return helpers.setStateProp(
        'update',
        {
          error: action.error,
          errorMessage: action.payload.message,
          delete: true
        },
        {
          state,
          initialState
        }
      );

    case sourcesTypes.UPDATE_SOURCE_REJECTED:
      return helpers.setStateProp(
        'update',
        {
          error: action.error,
          errorMessage: action.payload.message,
          edit: true
        },
        {
          state,
          initialState
        }
      );

    case sourcesTypes.GET_SOURCES_REJECTED:
      return helpers.setStateProp(
        'view',
        {
          error: action.error,
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
          sources: action.payload.data.results,
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
