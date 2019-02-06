import { credentialsTypes, sourcesTypes } from '../constants';
import helpers from '../../common/helpers';
import apiTypes from '../../constants/apiConstants';

const initialState = {
  view: {
    show: false,
    add: false,
    edit: false,
    allCredentials: [],
    source: {},
    error: false,
    errorMessage: null,
    stepOneValid: false,
    stepTwoValid: false,
    fulfilled: false
  }
};

const addSourceWizardReducer = (state = initialState, action) => {
  switch (action.type) {
    case sourcesTypes.CREATE_SOURCE_SHOW:
      return helpers.setStateProp(
        'view',
        {
          show: true,
          add: true,
          allCredentials: state.view.allCredentials
        },
        {
          state,
          initialState
        }
      );

    case sourcesTypes.EDIT_SOURCE_SHOW:
      return helpers.setStateProp(
        'view',
        {
          show: true,
          edit: true,
          source: action.source,
          stepOneValid: true
        },
        {
          state,
          initialState
        }
      );

    case sourcesTypes.UPDATE_SOURCE_HIDE:
      return helpers.setStateProp(
        'view',
        {
          show: false
        },
        {
          state,
          initialState
        }
      );

    case sourcesTypes.UPDATE_SOURCE_WIZARD_STEPONE:
      return helpers.setStateProp(
        'view',
        {
          source: action.source,
          stepOneValid: true
        },
        {
          state,
          reset: false
        }
      );

    case sourcesTypes.UPDATE_SOURCE_WIZARD_STEPTWO:
      return helpers.setStateProp(
        'view',
        {
          source: action.source,
          stepTwoValid: true
        },
        {
          state,
          reset: false
        }
      );

    case sourcesTypes.INVALID_SOURCE_WIZARD_STEPTWO:
      return helpers.setStateProp(
        'view',
        {
          stepTwoValid: false
        },
        {
          state,
          reset: false
        }
      );

    case helpers.REJECTED_ACTION(sourcesTypes.ADD_SOURCE):
      return helpers.setStateProp(
        'view',
        {
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload)
        },
        {
          state,
          reset: false
        }
      );

    case helpers.REJECTED_ACTION(sourcesTypes.UPDATE_SOURCE):
      return helpers.setStateProp(
        'view',
        {
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload)
        },
        {
          state,
          reset: false
        }
      );

    case helpers.FULFILLED_ACTION(sourcesTypes.UPDATE_SOURCE):
    case helpers.FULFILLED_ACTION(sourcesTypes.ADD_SOURCE):
      return helpers.setStateProp(
        'view',
        {
          source: action.payload.data,
          fulfilled: true
        },
        {
          state,
          reset: false
        }
      );

    case helpers.FULFILLED_ACTION(credentialsTypes.GET_WIZARD_CREDENTIALS):
      return helpers.setStateProp(
        'view',
        {
          allCredentials: (action.payload.data && action.payload.data[apiTypes.API_RESPONSE_CREDENTIALS_RESULTS]) || []
        },
        {
          state,
          reset: false
        }
      );

    default:
      return state;
  }
};

addSourceWizardReducer.initialState = initialState;

export { addSourceWizardReducer as default, initialState, addSourceWizardReducer };
