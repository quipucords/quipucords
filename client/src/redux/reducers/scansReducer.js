import * as types from '../constants/scansConstants';

const initialState = {
  data: []
};

export default function scansReducer(state = initialState, action) {
  switch (action.type) {
    case types.LOAD_SCANS_SUCCESS:
      return Object.assign({}, state, action.data);
    default:
      return state;
  }
}
