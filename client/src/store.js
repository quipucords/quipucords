import { createStore } from 'redux';

import appReducer from './reducers/appReducer';

const hydrateStore = () => {
  // Create any initial state items based on stored data (cookies etc.)
  return {
  };
};

const store = createStore(
  appReducer,
  hydrateStore()
);

export default store;
