import ClassNames from 'classnames';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';
import React, { Component } from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';
import { routes } from '../../routes';
import { withRouter } from 'react-router';

class Content extends Component {
  renderRoutes() {
    let redirectRoot = null;

    return {
      renderRoutes: routes().map((item, index) => {
        if (item.redirect === true) {
          redirectRoot = <Redirect from="/" to={item.to} />;
        }

        return <Route key={index} path={item.to} component={item.component} />;
      }),
      redirectRoot
    };
  }

  render() {
    let classes = ClassNames({
      'container-pf-nav-pf-vertical': true,
      'collapsed-nav': this.props.navigationBar.collapsed
    });

    const { renderRoutes, redirectRoot } = this.renderRoutes();

    return (
      <div className={classes}>
        <Switch>{renderRoutes}</Switch>
        {redirectRoot}
      </div>
    );
  }
}
Content.propTypes = {
  navigationBar: PropTypes.object
};

function mapStateToProps(state, ownProps) {
  return state;
}

export default withRouter(connect(mapStateToProps)(Content));
