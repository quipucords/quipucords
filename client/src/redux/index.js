import { connect } from 'react-redux';
import { withRouter } from 'react-router-dom';
import store from './store';
import reduxActions from './actions/index';
import reduxReducers from './reducers/index';
import reduxTypes from './constants/index';

const connectRouter = (mapStateToProps, mapDispatchToProps) => component =>
  withRouter(
    connect(
      mapStateToProps,
      mapDispatchToProps
    )(component)
  );

export { connect, connectRouter, reduxActions, reduxReducers, reduxTypes, store };
