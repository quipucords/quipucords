import { navigationBarTypes } from '../constants';

const initialState = {
  collapsed: false
};

export default function navigationBarReducer(state = initialState, action) {
  switch (action.type) {
    case navigationBarTypes.NAV_TOGGLE_COLLAPSE:
      return Object.assign({}, state, { collapsed: !state.collapsed });

    case navigationBarTypes.NAV_COLLAPSE:
      return Object.assign({}, state, { collapsed: true });

    case navigationBarTypes.NAV_OPEN:
      return Object.assign({}, state, { collapsed: false });

    default:
      return state;
  }
}
