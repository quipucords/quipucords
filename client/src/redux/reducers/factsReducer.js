import helpers from '../../common/helpers';
import { factsTypes } from '../constants';

const initialState = {
  update: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    facts: {}
  }
};

const factsReducer = (state = initialState, action) => {
  switch (action.type) {
    case helpers.REJECTED_ACTION(factsTypes.ADD_FACTS):
      return helpers.setStateProp(
        'update',
        {
          error: action.error,
          errorMessage: helpers.getMessageFromResults(action.payload).message
        },
        {
          state,
          initialState
        }
      );

    case helpers.PENDING_ACTION(factsTypes.ADD_FACTS):
      return helpers.setStateProp(
        'update',
        {
          pending: true
        },
        {
          state,
          initialState
        }
      );

    case helpers.FULFILLED_ACTION(factsTypes.ADD_FACTS):
      return helpers.setStateProp(
        'update',
        {
          facts: action.payload.data,
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

factsReducer.initialState = initialState;

export { factsReducer as default, initialState, factsReducer };
