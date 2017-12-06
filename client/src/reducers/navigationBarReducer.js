const initialState = {
  collapsed: false
};

export default function navigationBarReducer(state = initialState, action) {
  switch (action.type) {
    case 'NAV_TOGGLE_COLLAPSE':
      return Object.assign({}, state, {collapsed: !state.collapsed});

    case 'NAV_COLLAPSE':
      return Object.assign({}, state, {collapsed: true});

    case 'NAV_OPEN':
      return Object.assign({}, state, {collapsed: false});

    default:
      return state;
  }
}
