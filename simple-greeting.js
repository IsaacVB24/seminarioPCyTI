import { html, css, LitElement } from "lit";

export class SimpleGreeting extends LitElement {
  static styles = css`
    p {
      color: blue;
    }
  `;

  static properties = {
    name: { type: String },
  };

  constructor() {
    super();
    this.name = "Somebody";
    console.log("Constructor: name = ", this.name);
  }

  update(changedProperties) {
    super.update(changedProperties);
    console.log("Update: name = ", this.name);
  }

  render() {
    return html`<p>Hello, ${this.name}!</p>`;
  }
}
customElements.define("simple-greeting", SimpleGreeting);
