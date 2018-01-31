import React from 'react';
import PropTypes from 'prop-types';
import { OverlayTrigger, Tooltip } from 'patternfly-react';

const SimpleTooltip = ({ children, tooltip, placement, ...rest }) => {
  return (
    <OverlayTrigger
      overlay={<Tooltip {...rest}>{tooltip}</Tooltip>}
      placement={placement}
    >
      <span>{children}</span>
    </OverlayTrigger>
  );
};
SimpleTooltip.propTypes = {
  children: PropTypes.node,
  tooltip: PropTypes.node,
  placement: PropTypes.string
};

SimpleTooltip.defaultProps = {
  placement: 'top'
};

export { SimpleTooltip };
