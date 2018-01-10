
import * as types from '../constants/sourcesConstants';

const initialState = {
  data: []
};

export default function sourcesReducer(state=initialState, action) {
  switch(action.type) {
    case types.LOAD_SOURCES_SUCCESS:
      return Object.assign({}, state, action.data);
    default:
      return state;
  }
}
