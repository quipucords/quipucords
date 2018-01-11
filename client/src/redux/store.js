import { createStore, applyMiddleware } from 'redux';
import thunkMiddleware from 'redux-thunk';

import appReducer from './reducers/appReducer';

const hydrateStore = () => {
  // Create any initial state items based on stored data (cookies etc.)
  return {};
};

const store = createStore(
  appReducer,
  hydrateStore(),
  applyMiddleware(thunkMiddleware)
);

export default store;
