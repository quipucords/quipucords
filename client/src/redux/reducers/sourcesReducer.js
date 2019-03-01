import helpers from '../../common/helpers';
import { sourcesTypes } from '../constants';
import apiTypes from '../../constants/apiConstants';

const initialState = {
  view: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    sources: [],
    updateSources: false
  },

  update: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    sourceId: '',
    delete: false
  }
};

const sourcesReducer = (state = initialState, action) => {
  switch (action.type) {
    case sourcesTypes.UPDATE_SOURCES:
      return helpers.setStateProp(
        'view',
        {
          updateSources: true
        },
        {
          state,
          reset: false
        }
      );

    case helpers.REJECTED_ACTION(sourcesTypes.DELETE_SOURCE):
    case helpers.REJECTED_ACTION(sourcesTypes.DELETE_SOURCES):
      return helpers.setStateProp(
        'update',
        {
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload).message,
          delete: true
        },
        {
          state,
          initialState
        }
      );

    case helpers.PENDING_ACTION(sourcesTypes.DELETE_SOURCE):
    case helpers.PENDING_ACTION(sourcesTypes.DELETE_SOURCES):
      return helpers.setStateProp(
        'update',
        {
          pending: true,
          delete: true
        },
        {
          state,
          initialState
        }
      );

    case helpers.FULFILLED_ACTION(sourcesTypes.DELETE_SOURCE):
    case helpers.FULFILLED_ACTION(sourcesTypes.DELETE_SOURCES):
      return helpers.setStateProp(
        'update',
        {
          fulfilled: true,
          delete: true
        },
        {
          state,
          initialState
        }
      );

    case helpers.REJECTED_ACTION(sourcesTypes.GET_SOURCES):
      return helpers.setStateProp(
        'view',
        {
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload).message
        },
        {
          state,
          initialState
        }
      );

    case helpers.PENDING_ACTION(sourcesTypes.GET_SOURCES):
      return helpers.setStateProp(
        'view',
        {
          pending: true,
          sources: state.view.sources
        },
        {
          state,
          initialState
        }
      );

    case helpers.FULFILLED_ACTION(sourcesTypes.GET_SOURCES):
      return helpers.setStateProp(
        'view',
        {
          sources: (action.payload.data && action.payload.data[apiTypes.API_RESPONSE_SOURCES_RESULTS]) || [],
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

sourcesReducer.initialState = initialState;

export { sourcesReducer as default, initialState, sourcesReducer };
