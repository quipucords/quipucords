import React from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';
import { routes } from '../../routes';

class Content extends React.Component {
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
    const { renderRoutes, redirectRoot } = this.renderRoutes();

    return (
      <div className="quipucords-content">
        <Switch>
          {renderRoutes}
          {redirectRoot}
        </Switch>
      </div>
    );
  }
}

export default Content;
