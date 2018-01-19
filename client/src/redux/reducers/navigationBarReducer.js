import { navigationBarTypes as types } from '../constants';

const initialState = {
  collapsed: false
};

export default function navigationBarReducer(state = initialState, action) {
  switch (action.type) {
    case types.NAV_TOGGLE_COLLAPSE:
      return Object.assign({}, state, { collapsed: !state.collapsed });

    case types.NAV_COLLAPSE:
      return Object.assign({}, state, { collapsed: true });

    case types.NAV_OPEN:
      return Object.assign({}, state, { collapsed: false });

    default:
      return state;
  }
}
